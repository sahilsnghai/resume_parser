import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

from app.core.config import settings
from app.schemas import ResumeDataSchema
from app.utils.logger import get_logger, log_llm_success

logger = get_logger("app.services.llm_service")


class ResumeExtractionPrompt:
    """Prompt templates for resume extraction"""

    SYSTEM_PROMPT = """
You are an expert resume parser with extensive experience in extracting structured information from resumes and CVs.

Your task is to analyze the provided resume text and extract the following information in a structured JSON format:

1. **Contact Information**: Extract full name, email, phone number, and location (city, state/country).
2. **Professional Summary**: Extract the professional summary, objective, or profile statement if present.
3. **Work Experience**: Extract all work experiences including job title, company name, duration, and key responsibilities/achievements.
4. **Education**: Extract all educational qualifications including degree, institution, and year of completion.
5. **Skills**: Categorize skills into technical skills and soft skills.
6. **Certifications**: Extract any professional certifications or licenses.


- Analyze the text carefully and extract ALL relevant information
- If information is missing or unclear, set the field to null or empty list
- For work experience, list experiences in reverse chronological order (most recent first)
- For education, list in reverse chronological order (highest degree first)
- Extract skills and categorize them appropriately
- Use the exact JSON schema provided below


You MUST return a valid JSON object that matches the provided Pydantic schema exactly.
Do not add any text before or after the JSON object.
Only return the JSON object with the extracted data.
"""

    HUMAN_PROMPT_TEMPLATE = """
Please extract structured information from the following resume text:

<resume_text>
{resume_text}
</resume_text>

Extract the information and return it in the exact JSON format specified by the schema.
Remember to return ONLY the JSON object, nothing before or after it.
"""


class LLMService:
    """Service for LLM operations"""

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

        self.raw_llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.openai_api_key,
        )
        self.llm = self.raw_llm.with_structured_output(ResumeDataSchema)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ResumeExtractionPrompt.SYSTEM_PROMPT),
                ("human", ResumeExtractionPrompt.HUMAN_PROMPT_TEMPLATE),
            ]
        )

        self.output_parser = PydanticOutputParser(pydantic_object=ResumeDataSchema)

        logger.info(f"LLM Service initialized with model: {self.model_name}")

    async def extract_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract structured resume data from text using GPT-4

        Args:
            resume_text (str): Raw resume text

        Returns:
            Dict[str, Any]: Extracted resume data

        Raises:
            Exception: If extraction fails after retries
        """
        logger.info(
            f"Starting resume data extraction for text length: {len(resume_text)}"
        )

        messages = self.prompt.format_prompt(resume_text=resume_text).to_messages()

        max_retries = 1
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"LLM extraction attempt {attempt + 1}/{max_retries}")

                start_time = datetime.now()
                response = await self._call_llm(messages)
                end_time = datetime.now()

                processing_time = (end_time - start_time).total_seconds()

                log_llm_success("resume_extraction", processing_time)

                logger.info(
                    f"Successfully extracted resume data in {processing_time:.2f} seconds"
                )
                return response.model_dump()

            except OutputParserException as e:
                logger.error(f"Output parsing failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Failed to parse LLM response after {max_retries} attempts: {e}"
                    )

            except Exception as e:
                logger.error(f"LLM extraction failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Failed to extract resume data after {max_retries} attempts: {e}"
                    )

                await asyncio.sleep(retry_delay * (2**attempt))

        raise Exception("Unexpected error in resume extraction")

    async def _call_llm(self, messages: List) -> ResumeDataSchema:
        """
        Call LLM with retry logic

        Args:
            messages: List of messages for LLM

        Returns:
            str: LLM response content
        """
        try:
            response = await self.llm.ainvoke(messages)

            return response

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    async def _parse_llm_response(self, response_content: str) -> ResumeDataSchema:
        """
        Parse LLM response into structured data

        Args:
            response_content (str): Raw LLM response

        Returns:
            ResumeDataSchema: Parsed structured data

        Raises:
            OutputParserException: If parsing fails
        """
        try:
            logger.debug(
                f"Attempting to parse LLM response: {response_content[:200]}..."
            )

            try:
                json_data = json.loads(response_content)
                return ResumeDataSchema.model_validate(json_data)
            except json.JSONDecodeError:
                pass

            return self.output_parser.parse(response_content)

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response content: {response_content}")
            raise OutputParserException(f"Failed to parse LLM response: {e}")

    def validate_extracted_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate extracted resume data

        Args:
            data (Dict[str, Any]): Extracted data

        Returns:
            bool: True if data is valid
        """
        try:
            ResumeDataSchema.parse_obj(data)
            return True
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False


class ResumeExtractionChain:
    """Orchestrates resume extraction using LangChain components"""

    def __init__(self):
        self.llm_service = LLMService()

    async def extract_from_text(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract resume data from text with preprocessing

        Args:
            resume_text (str): Raw resume text

        Returns:
            Dict[str, Any]: Extracted resume data
        """
        logger.info("Starting resume extraction chain")

        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty")

        cleaned_text = self._preprocess_text(resume_text)

        logger.info(f"Processing text length: {len(cleaned_text)} characters")

        if len(cleaned_text) > 8000:
            logger.info("Text is long, will process in chunks")
            return await self._extract_from_chunks(cleaned_text)
        else:
            return await self.llm_service.extract_resume_data(cleaned_text)

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess resume text

        Args:
            text (str): Raw text

        Returns:
            str: Processed text
        """

        text = " ".join(text.split())

        import re

        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"\t+", " ", text)

        return text.strip()

    async def _extract_from_chunks(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract data from multiple text chunks and combine results

        Args:
            resume_text (str): Long resume text

        Returns:
            Dict[str, Any]: Combined extracted data
        """
        from app.utils.extractor import chunk_for_llm

        chunks = chunk_for_llm(resume_text, chunk_size=4000, overlap=500)
        logger.info(f"Text chunked into {len(chunks)} pieces")

        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            try:
                result = await self.llm_service.extract_resume_data(chunk)
                chunk_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}: {e}")
                continue

        if not chunk_results:
            raise Exception("Failed to extract data from any chunks")

        return self._combine_chunk_results(chunk_results)

    def _combine_chunk_results(
        self, chunk_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine results from multiple chunks

        Args:
            chunk_results (List[Dict[str, Any]]): List of chunk results

        Returns:
            Dict[str, Any]: Combined result
        """
        if len(chunk_results) == 1:
            return chunk_results[0]

        combined = chunk_results[0].copy()

        if "contact_info" in combined and combined["contact_info"]:

            pass

        for key in ["work_experience", "education", "certifications"]:
            combined[key] = []
            seen_items = set()

            for result in chunk_results:
                if key in result and result[key]:
                    for item in result[key]:

                        if key == "work_experience":
                            identifier = (
                                f"{item.get('role', '')}-{item.get('company', '')}"
                            )
                        elif key == "education":
                            identifier = f"{item.get('degree', '')}-{item.get('institution', '')}"
                        elif key == "certifications":
                            identifier = item.get("name", "")
                        else:
                            identifier = str(item)

                        if identifier and identifier not in seen_items:
                            combined[key].append(item)
                            seen_items.add(identifier)

        if "skills" in combined:
            technical_skills = set()
            soft_skills = set()

            for result in chunk_results:
                if "skills" in result and result["skills"]:
                    if "technical_skills" in result["skills"]:
                        technical_skills.update(result["skills"]["technical_skills"])
                    if "soft_skills" in result["skills"]:
                        soft_skills.update(result["skills"]["soft_skills"])

            combined["skills"]["technical_skills"] = list(technical_skills)
            combined["skills"]["soft_skills"] = list(soft_skills)

        best_summary = ""
        for result in chunk_results:
            if (
                "summary" in result
                and result["summary"]
                and len(result["summary"]) > len(best_summary)
            ):
                best_summary = result["summary"]

        combined["summary"] = best_summary

        return combined


llm_service = LLMService()
extraction_chain = ResumeExtractionChain()
