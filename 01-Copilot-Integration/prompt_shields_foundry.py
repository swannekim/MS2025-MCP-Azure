#
# Copyright (c) Microsoft. All rights reserved.
# To learn more, please visit the documentation - Quickstart: Azure Content Safety: https://aka.ms/acsstudiodoc
#
import requests

def shield_prompt_body(
    user_prompt: str,
    documents: list
) -> dict:
    """
    Builds the request body for the Content Safety API request.

    Args:
    - user_prompt (str): The user prompt to analyze.
    - documents (list): The documents to analyze.

    Returns:
    - dict: The request body for the Content Safety API request.
    """
    body = {
        "userPrompt": user_prompt,
        "documents": documents
    }
    return body

def detect_groundness_result(
    data: dict,
    url: str,
    subscription_key: str
):
    """
    Retrieve the Content Safety API request result.

    Args:
    - data (dict): The body data sent in the request.
    - url (str): The URL address of the request being sent.
    - subscription_key (str): The subscription key value corresponding to the request being sent.

    Returns:
    - response: The request result of the Content Safety API.
    """
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": subscription_key
    }

    # Send the API request
    response = requests.post(url, headers=headers, json=data)
    return response

# if __name__ == "__main__":
#     # Replace with your own subscription_key and endpoint
#     subscription_key = "<your_subscription_key>"
#     endpoint = "<your_resource_endpoint>"

#     api_version = "2024-09-01"

#     # Set according to the actual task category.
#     user_prompt = "<test_user_prompt>"
#     documents = [
#         "<this_is_a_documents>",
#         "<this_is_another_documents>"
#     ]

#     # Build the request body
#     data = shield_prompt_body(user_prompt=user_prompt, documents=documents)
#     # Set up the API request
#     url = f"{endpoint}/contentsafety/text:shieldPrompt?api-version={api_version}"

#     # Send the API request
#     response = detect_groundness_result(data=data, url=url, subscription_key=subscription_key)

#     # Handle the API response
#     if response.status_code == 200:
#         result = response.json()
#         print("shieldPrompt result:", result)
#     else:
#         print("Error:", response.status_code, response.text)

def check_prompt_attack(user_prompt: str, documents: list, endpoint: str, subscription_key: str, api_version: str = "2024-09-01") -> bool:
    """샘플 코드 사용: 공격 탐지 여부만 True/False로 반환."""
    if not endpoint or not subscription_key:
        # 설정 비어있으면 검사 스킵(워크샵 편의)
        return False

    url = f"{endpoint.rstrip('/')}/contentsafety/text:shieldPrompt?api-version={api_version}"
    data = shield_prompt_body(user_prompt=user_prompt or "", documents=documents or [])
    resp = detect_groundness_result(data=data, url=url, subscription_key=subscription_key)

    if resp.status_code != 200:
        # 운영에서는 차단 권장. 실습에선 로그만 보고 통과시킬 수도 있음.
        raise RuntimeError(f"Content Safety error {resp.status_code}: {resp.text[:200]}")

    result = resp.json()
    up = result.get("userPromptAnalysis", {}).get("attackDetected", False)
    doc_flags = [d.get("attackDetected", False) for d in result.get("documentsAnalysis", [])]
    return bool(up or any(doc_flags))
