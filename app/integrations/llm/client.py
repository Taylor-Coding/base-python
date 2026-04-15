import logging
from collections.abc import Iterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Ollama 기반 LangChain 클라이언트.

    사용 예시:
        client = LLMClient()

        # 단순 텍스트 응답
        answer = client.invoke("파이썬의 장점을 알려줘")

        # 시스템 프롬프트 포함
        answer = client.invoke("요약해줘", system="당신은 요약 전문가입니다.")

        # 스트리밍
        for chunk in client.stream("긴 글을 써줘"):
            print(chunk, end="", flush=True)

        # 커스텀 체인 구성
        chain = client.chain(prompt_template)
        result = chain.invoke({"topic": "FastAPI"})
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
    ) -> None:
        resolved_model = model or settings.LLM_MODEL
        resolved_base_url = base_url or settings.LLM_BASE_URL

        if not resolved_model or not resolved_base_url:
            raise LLMNotConfiguredError()

        self._llm = ChatOllama(
            model=resolved_model,
            base_url=resolved_base_url,
            temperature=temperature,
        )

    # ── 단순 호출 ────────────────────────────────────────────

    def invoke(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        logger.debug("LLM invoke: model=%s, prompt_len=%d", self._llm.model, len(prompt))
        response: AIMessage = self._llm.invoke(messages)
        return str(response.content)

    def stream(self, prompt: str, system: str | None = None) -> Iterator[str]:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        logger.debug("LLM stream: model=%s", self._llm.model)
        for chunk in self._llm.stream(messages):
            yield str(chunk.content)

    # ── 체인 구성 ────────────────────────────────────────────

    def chain(self, prompt: ChatPromptTemplate) -> Runnable:
        """프롬프트 템플릿과 LLM을 연결한 체인을 반환한다.

        사용 예시:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 {role}입니다."),
                ("human", "{question}"),
            ])
            chain = client.chain(prompt)
            result = chain.invoke({"role": "번역가", "question": "Hello를 번역해줘"})
        """
        return prompt | self._llm | StrOutputParser()

    @property
    def llm(self) -> ChatOllama:
        """LangChain 모델 인스턴스를 직접 사용해야 할 때."""
        return self._llm


class LLMNotConfiguredError(Exception):
    """LLM 설정(LLM_BASE_URL, LLM_MODEL)이 없을 때 발생하는 예외."""

    def __init__(self) -> None:
        super().__init__("LLM이 설정되지 않았습니다. LLM_BASE_URL과 LLM_MODEL을 확인하세요.")
