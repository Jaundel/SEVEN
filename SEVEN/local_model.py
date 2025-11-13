# ============================================================
#  File: local_model.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Interface for invoking the local Lemonade Server model.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Local Lemonade Server adapter for SEVEN's energy-aware router.

Usage (for router integration):
    from local_model import ask_local, LocalModelResponse, LemonadeClientError

    try:
        response = ask_local("What is the capital of France?")
        print(f"Answer: {response.text}")
        print(f"Latency: {response.latency_s:.2f}s")
        print(f"Tokens: {response.tokens_used}")
    except LemonadeClientError as e:
        print(f"Local model failed: {e}")

Environment Variables (all optional):
    LEMONADE_BASE_URL: Base URL for Lemonade Server (default: http://localhost:8000/api/v1)
    LEMONADE_MODEL: Model name to use (default: Llama-3.2-1B-Instruct-Hybrid)
    LEMONADE_RECIPE: Recipe for hybrid routing, e.g., "oga-hybrid" (default: None)
    LEMONADE_DEVICE: Device selector: "cpu", "gpu", "hybrid" (default: None)
    LEMONADE_TIMEOUT_SECONDS: HTTP timeout in seconds (default: 30.0)
    LEMONADE_MAX_RETRIES: Max retry attempts for failed requests (default: 2)
    LEMONADE_BACKOFF_SECONDS: Initial retry backoff interval (default: 0.5)
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin

# for api tools
from api_tools import detect_api_intent, get_weather, get_crypto_price, get_news
def ask_local_with_api(prompt: str):
    """
    Intelligently determine if APIs are needed for real-time data.
    Only trigger APIs if the query requires current/live information.
    Otherwise, use the local model for general knowledge questions.
    """
    import json

    # Step 1: Ask local model to classify if APIs are needed
    classification_prompt = (
        "Analyze this user query and determine if it requires real-time data from external APIs.\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        '{"needs_api": true/false, "apis": ["weather", "crypto", "news"]}\n\n'
        "Guidelines:\n"
        "- needs_api: true ONLY if the query asks for CURRENT/LIVE data (current weather, latest news, current prices)\n"
        "- needs_api: false for general knowledge, definitions, explanations, historical info\n"
        "- apis: list which specific APIs are needed (empty array if needs_api is false)\n\n"
        f"User query: {prompt}\n\n"
        "Response:"
    )

    try:
        classification_response = ask_local(classification_prompt, max_tokens=100, temperature=0.3)
        # Clean up the response - remove markdown code blocks if present
        response_text = classification_response.text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            classification = json.loads(response_text)
            needs_api = classification.get("needs_api", False)
            apis_needed = classification.get("apis", [])
            
            # Validate the structure
            if not isinstance(needs_api, bool) or not isinstance(apis_needed, list):
                raise ValueError("Invalid classification structure")
                
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: if parsing fails, assume no API needed
            print(f"Classification parsing failed: {e}, defaulting to local model")
            needs_api = False
            apis_needed = []
            
    except Exception as e:
        print(f"Classification failed: {e}, defaulting to local model")
        needs_api = False
        apis_needed = []

    # Step 2: If no API needed, return local model response directly
    if not needs_api:
        try:
            response = ask_local(prompt)
            return response
        except Exception as e:
            return LocalModelResponse(
                prompt=prompt,
                text=f"Error generating response: {e}",
                model="error",
                latency_s=0.0,
                tokens_used=None,
                raw={}
            )

    # Step 3: Call the required APIs
    api_results = []
    
    if "weather" in apis_needed:
        try:
            weather_data = get_weather(prompt)
            api_results.append(f"Weather: {weather_data}")
        except Exception as e:
            api_results.append(f"Weather API error: {e}")
    
    if "crypto" in apis_needed:
        try:
            crypto_data = get_crypto_price(prompt)
            api_results.append(f"Crypto: {crypto_data}")
        except Exception as e:
            api_results.append(f"Crypto API error: {e}")
    
    if "news" in apis_needed:
        try:
            news_data = get_news(prompt)
            api_results.append(f"News: {news_data}")
        except Exception as e:
            api_results.append(f"News API error: {e}")

    # Step 4: If APIs returned data, synthesize a response
    if api_results:
        api_context = "\n".join(api_results)
        synthesis_prompt = (
            f"Based on this real-time data, answer the user's question naturally:\n\n"
            f"Real-time data:\n{api_context}\n\n"
            f"User question: {prompt}\n\n"
            f"Provide a clear, natural answer:"
        )
        try:
            final_response = ask_local(synthesis_prompt, max_tokens=256)
            return final_response
        except Exception as e:
            # If synthesis fails, return raw API results
            return LocalModelResponse(
                prompt=prompt,
                text=api_context,
                model="api-direct",
                latency_s=0.0,
                tokens_used=None,
                raw={}
            )
    
    # Step 5: If APIs were requested but failed, fallback to local model
    try:
        fallback_response = ask_local(
            f"{prompt}\n\n(Note: Real-time data APIs were unavailable, providing general knowledge response)"
        )
        return fallback_response
    except Exception as e:
        return LocalModelResponse(
            prompt=prompt,
            text=f"Unable to process request: {e}",
            model="error",
            latency_s=0.0,
            tokens_used=None,
            raw={}
        )


import requests

LOGGER = logging.getLogger(__name__)
DEFAULT_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_MODEL = "Llama-3.2-1B-Instruct-Hybrid"
DEFAULT_RECIPE = ""
DEFAULT_DEVICE = ""
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF = 0.5


class Spinner:
    """Simple terminal spinner for showing progress."""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.spinner_chars = "|/-\\"
        self.running = False
        self.thread = None

    def _spin(self):
        """Run the spinner animation."""
        idx = 0
        while self.running:
            char = self.spinner_chars[idx % len(self.spinner_chars)]
            sys.stdout.write(f"\r{self.message}... {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1

    def start(self):
        """Start the spinner in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 6) + "\r")
        sys.stdout.flush()


class LemonadeClientError(RuntimeError):
    """Raised when a Lemonade Server call fails."""


@dataclass
class LocalModelResponse:
    """Normalized response returned to the router layer.

    Fields:
        prompt: The original user prompt sent to the model
        text: Generated text response from the model
        model: Actual model identifier used (e.g., "amd/Phi-3.5-mini-instruct-onnx-ryzenai-npu")
        latency_s: Total round-trip latency in seconds
        tokens_used: Total tokens consumed (prompt + completion), or None if unavailable
        raw: Full raw JSON response from Lemonade Server for advanced debugging
    """

    prompt: str
    text: str
    model: str
    latency_s: float
    tokens_used: Optional[int]
    raw: Dict[str, Any]


def _base_url() -> str:
    """Return the Lemonade Server base URL from the environment.

    Returns:
        str: Base URL with trailing slash removed.

    Raises:
        None.

    TODO:
        * Allow per-branch overrides via YAML when multiple servers run locally.
    """
    return os.getenv("LEMONADE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _model_name() -> str:
    """Return the model name or fall back to the default hybrid model."""
    return os.getenv("LEMONADE_MODEL", DEFAULT_MODEL)


def _recipe() -> Optional[str]:
    """Return the Lemonade recipe (e.g., oga-hybrid) for hybrid routing."""
    value = os.getenv("LEMONADE_RECIPE", DEFAULT_RECIPE).strip()
    return value or None


def _device() -> Optional[str]:
    """Return the target device selector (cpu/gpu/hybrid)."""
    value = os.getenv("LEMONADE_DEVICE", DEFAULT_DEVICE).strip()
    return value or None


def _timeout() -> float:
    """Return the HTTP timeout in seconds."""
    raw_timeout = os.getenv("LEMONADE_TIMEOUT_SECONDS")
    return float(raw_timeout) if raw_timeout else DEFAULT_TIMEOUT


def _max_retries() -> int:
    """Return the maximum number of retry attempts for Lemonade calls."""
    raw_value = os.getenv("LEMONADE_MAX_RETRIES")
    try:
        return int(raw_value) if raw_value is not None else DEFAULT_MAX_RETRIES
    except ValueError as exc:
        raise LemonadeClientError("LEMONADE_MAX_RETRIES must be an integer.") from exc


def _backoff_seconds() -> float:
    """Return the initial backoff interval between retries."""
    raw_value = os.getenv("LEMONADE_BACKOFF_SECONDS")
    try:
        return float(raw_value) if raw_value is not None else DEFAULT_BACKOFF
    except ValueError as exc:
        raise LemonadeClientError("LEMONADE_BACKOFF_SECONDS must be a float.") from exc


def _parse_response(data: Dict[str, Any], *, prompt: str, latency: float) -> LocalModelResponse:
    """Validate and normalize the Lemonade response payload.

    Args:
        data: Parsed JSON payload from Lemonade Server.
        prompt: Original user prompt text.
        latency: Total round-trip time in seconds.

    Returns:
        LocalModelResponse: Structured response ready for the router.

    Raises:
        LemonadeClientError: If required fields are missing from the payload.
    """
    choices = data.get("choices")
    if not choices:
        raise LemonadeClientError("Lemonade response missing 'choices'.")

    message = choices[0].get("message")
    if not message or "content" not in message:
        raise LemonadeClientError("Lemonade response missing message content.")

    text = message["content"]
    if text is None:
        raise LemonadeClientError("Lemonade response contained null content.")

    usage = data.get("usage") or {}
    total_tokens = usage.get("total_tokens")
    if total_tokens is not None:
        try:
            total_tokens = int(total_tokens)
        except (TypeError, ValueError) as exc:
            raise LemonadeClientError("Invalid token count in Lemonade response.") from exc

    return LocalModelResponse(
        prompt=prompt,
        text=text.strip(),
        model=data.get("model") or _model_name(),
        latency_s=latency,
        tokens_used=total_tokens,
        raw=data,
    )


def _should_retry(status_code: int) -> bool:
    """Determine whether the HTTP response merits a retry."""
    return 500 <= status_code < 600


def ask_local(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 128,
    stream: bool = False,
    recipe: Optional[str] = None,
    device: Optional[str] = None,
    timeout: Optional[float] = None,
) -> LocalModelResponse:
    """Send prompts to the local Lemonade Server model.

    Args:
        prompt: Primary user prompt to execute locally.
        system_prompt: Optional instruction layer injected before the user text.
        temperature: Sampling temperature used for chat completions.
        max_tokens: Maximum number of tokens to generate in the completion.
        stream: Whether to request SSE streaming (currently unused).
        recipe: Lemonade recipe identifier (e.g., "oga-hybrid") for hybrid routing.
        device: Explicit device selector ("cpu", "gpu", "hybrid") if supported.
        timeout: Optional per-call timeout override in seconds.

    Returns:
        LocalModelResponse: Normalized text, token usage, and latency data.

    Raises:
        ValueError: If the prompt is empty.
        LemonadeClientError: When the Lemonade request fails or the payload is invalid.

    TODO:
        * Implement streaming mode using Lemonade's SSE endpoint when router supports it.
        * Attach energy metadata (NPU vs GPU) once /system-info is integrated.
        * Surface recipe/device defaults inside the README for ops clarity.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    spinner = Spinner("Processing Locally")
    spinner.start()
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt.strip()})

        payload: Dict[str, Any] = {
            "model": _model_name(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        applied_recipe = recipe if recipe else _recipe()
        applied_device = device if device else _device()
        if applied_recipe:
            payload["recipe"] = applied_recipe
        if applied_device:
            payload["device"] = applied_device

        url = urljoin(f"{_base_url()}/", "chat/completions")
        call_timeout = timeout or _timeout()
        backoff = _backoff_seconds()

        attempt = 0
        max_attempts = _max_retries()
        while attempt <= max_attempts:
            start = time.perf_counter()
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=call_timeout,
                    headers={"Content-Type": "application/json"},
                )
            except requests.RequestException as exc:
                if attempt >= max_attempts:
                    raise LemonadeClientError(f"Lemonade request failed: {exc}") from exc
                LOGGER.warning("Lemonade call failed (%s). Retrying in %.2fs.", exc, backoff)
                time.sleep(backoff)
                backoff *= 2
                attempt += 1
                continue

            latency = time.perf_counter() - start

            if response.status_code >= 400:
                should_retry = _should_retry(response.status_code) and attempt < max_attempts
                try:
                    error_payload = response.json()
                except ValueError:
                    error_payload = {"error": {"message": response.text}}

                LOGGER.error("Lemonade error response (%s): %s", response.status_code, error_payload)

                message = error_payload.get("error", {}).get(
                    "message", f"HTTP {response.status_code}"
                )
                if should_retry:
                    LOGGER.warning(
                        "Retryable Lemonade error (%s). Retrying in %.2fs.", message, backoff
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    attempt += 1
                    continue
                raise LemonadeClientError(f"Lemonade Server error: {message}")

            try:
                data = response.json()
            except ValueError as exc:
                raise LemonadeClientError("Failed to parse Lemonade JSON response.") from exc

            result = _parse_response(data, prompt=prompt, latency=latency)
            return result

        raise LemonadeClientError("Exhausted Lemonade retries without a successful call.")
    finally:
        spinner.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if len(sys.argv) < 2:
        print("Usage: python local_model.py \"your prompt here\"")
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])

    try:
        # Use the new API-aware version
        response = ask_local_with_api(user_prompt)

        # If it's an API result (string), print it directly
        if isinstance(response, str):
            print("=== API RESULT ===")
            print(response)
        else:
            # Otherwise, it's a LocalModelResponse object
            print("=== Lemonade Local Test ===")
            print(f"Model:   {response.model}")
            print(f"Latency: {response.latency_s:.2f}s")
            print(f"Tokens:  {response.tokens_used if response.tokens_used is not None else 'N/A'}")
            print(f"Output:  {response.text}")

    except Exception as exc:
        print(f"Lemonade local test failed: {exc}")
