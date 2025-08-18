> 하단의 내용은 [MCP in Action: Real-World Case Studies](https://github.com/microsoft/mcp-for-beginners/blob/16039eb5fd6a26cb5e4e36d241a86c21d6d77aad/09-CaseStudy/apimsample.md) 를 참조하여 작성되었습니다.

# Case Study: Azure API Management의 REST API를 MCP 서버로 노출하기

Azure API Management(APIM)는 API 엔드포인트 앞단의 **게이트웨이**로 동작하며, 들어오는 요청을 프록시/정책 기반으로 제어합니다. APIM을 사용하면 다음과 같은 기능을 쉽게 추가할 수 있습니다:

* **보안(Security)**: API Key, JWT, Managed Identity 등 다양한 인증/인가 방식을 적용 가능. ([learn.microsoft.com][1])
* **요청 제어(Rate limiting)**: 단위 시간당 허용 호출 수를 제한하여 사용자 경험을 보호하고 백엔드 과부하를 방지. ([learn.microsoft.com][2])
* **스케일링 & 로드밸런싱**: 여러 백엔드로 부하 분산 및 확장 전략 구성. ([learn.microsoft.com][3])
* **AI 게이트웨이 기능(시맨틱 캐싱, 토큰 한도/모니터링 등)**: 지연시간 단축, 토큰 비용 가시화·제한 등 지능형 정책 제공. ([learn.microsoft.com][4], [TECHCOMMUNITY.MICROSOFT.COM][5])

## 왜 MCP + Azure API Management인가?

MCP(Model Context Protocol)는 에이전틱 애플리케이션에서 **도구와 데이터 노출의 표준**으로 빠르게 자리 잡고 있습니다. MCP 서버는 종종 외부 API를 호출해 툴 요청을 처리하므로, **API 관리를 위한 표준 게이트웨이인 APIM**과 결합하면 운영·보안·거버넌스 면에서 자연스러운 선택이 됩니다. ([learn.microsoft.com][3])

## Overview

해당 사례에서는 **REST API 엔드포인트를 MCP 서버로 노출**해, 에이전트 앱에서 바로 사용할 수 있도록 하면서 APIM의 기능(보안/정책/관측성)을 함께 활용하는 방법을 다룹니다.

## Key Features

* MCP **툴로 노출할 HTTP 메서드/오퍼레이션**을 선택적으로 지정.
* 부가 기능은 APIM **정책(Policy)** 구성에 따라 달라지며, 예시로 **rate limiting 정책** 적용을 보여줍니다. ([learn.microsoft.com][2])

---

## 사전 단계: API 가져오기(Import)

> 이미 APIM에 API가 있다면 이 단계를 건너뜁니다. 없다면 **OpenAPI/URL/리소스**에서 API를 가져오는 방법을 참고하세요. [MS Learn Tutorial: Import and publish your first API](https://learn.microsoft.com/en-us/azure/api-management/import-and-publish)

---

## REST API를 MCP 서버로 노출하기
> 자세한 내용은 [MS Learn: Expose REST API in API Management as an MCP server](https://learn.microsoft.com/en-us/azure/api-management/export-rest-mcp-server)에 제시되어 있습니다.

1. **Azure Portal** 접속 → APIM 인스턴스로 이동
   (빠른 진입 링크: `<https://portal.azure.com/?Microsoft_Azure_ApiManagement=mcp>`).

2. 좌측 메뉴 **APIs > MCP Servers > + Create new MCP Server** 선택.

3. **API** 섹션에서 MCP 서버로 노출할 **REST API** 선택.

4. MCP **툴로 노출할 오퍼레이션**(엔드포인트)을 1개 이상 선택(전부 or 일부).

5. **Create** 클릭.

6. **APIs > MCP Servers**로 이동하면, 생성된 MCP 서버 목록과 **엔드포인트 URL**을 확인할 수 있습니다(테스트/클라이언트에서 호출).

> 🔎 **전송(Transport) 참고:** VS Code 등 MCP 클라이언트는 **SSE** 또는 **Streamable HTTP**를 지원합니다. APIM 문서의 MCP 서버 기능은 최신 **Streamable HTTP**를 기본으로 안내하며, 문서의 예시 URL은 `/sse`(SSE) 또는 `/mcp`(HTTP)처럼 구분됩니다. 실 환경에서는 클라이언트/서버가 동일 전송을 지원하는지 확인하세요.

---

## (Optional) 정책 구성: Rate Limiting 예시

APIM 정책은 XML로 작성하며, **요청 제한(rate limit)**, **시맨틱 캐싱**, **토큰 한도** 등 다양한 규칙을 설정할 수 있습니다. 아래는 **클라이언트 IP 기준, 30초에 5회**로 제한하는 예시입니다. ([learn.microsoft.com][2])

```xml
<rate-limit-by-key 
  calls="5"
  renewal-period="30"
  counter-key="@(context.Request.IpAddress)"
  remaining-calls-variable-name="remainingCallsPerIP" />
```

정책 편집 경로: **APIs > MCP Servers > (대상 서버) > Policies** 에서 XML 편집.

> ⚠️ **스트리밍 주의:** MCP는 스트리밍이 핵심입니다. MCP 서버 정책에서 `context.Response.Body`에 접근하면 **버퍼링이 발생**해 스트리밍이 깨질 수 있으니 피하세요. 또한 App Insights/진단 로깅에서 **응답 바이트 로깅을 0**으로 두는 등, 페이로드 로깅으로 스트림이 방해받지 않도록 설정하세요. ([learn.microsoft.com][8])

---

## 사용해보기(Try it out): VS Code + Copilot Agent 모드

VS Code에서 MCP 서버를 등록하여 **에이전트 모드**로 툴을 호출해 봅니다. (방법은 **Command Palette의 `MCP: Add Server`** 또는 설정 파일 편집) ([code.visualstudio.com][9])

1. **Command Palette** → `MCP: Add Server`. ([code.visualstudio.com][9])
2. 서버 타입: **HTTP (HTTP or Server Sent Events)** 선택. ([code.visualstudio.com][9])
3. APIM에 표시된 MCP URL 입력(예):

   * SSE: `https://<apim>.azure-api.net/<api-name>-mcp/sse`
   * HTTP: `https://<apim>.azure-api.net/<api-name>-mcp/mcp`
4. 임의의 **Server ID** 지정. 저장 위치는 **Workspace(.vscode/mcp.json)** 또는 **User settings** 중 선택. ([code.visualstudio.com][9])

**Workspace 설정 예(.vscode/mcp.json):**

```json
{
  "servers": {
    "APIM petstore": {
      "type": "sse",
      "url": "https://<apim>.azure-api.net/<api-name>-mcp/sse"
    }
  }
}
```

**Streamable HTTP 전송 사용 시:**

```json
{
  "servers": {
    "APIM petstore": {
      "type": "http",
      "url": "https://<apim>.azure-api.net/<api-name>-mcp/mcp"
    }
  }
}
```

**인증 헤더 추가(Ocp-Apim-Subscription-Key):**

* VS Code **settings** UI에서 헤더 프롬프트를 추가하거나,
* `mcp.json`에 입력 프롬프트와 헤더를 선언합니다:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "apim_key",
      "description": "API Key for Azure API Management",
      "password": true
    }
  ],
  "servers": {
    "APIM petstore": {
      "type": "http",
      "url": "https://<apim>.azure-api.net/<api-name>-mcp/mcp",
      "headers": {
        "Ocp-Apim-Subscription-Key": "${input:apim_key}"
      }
    }
  }
}
```

> ✅ **정확한 헤더 사용 팁:** APIM의 **구독 키**는 기본적으로 `Ocp-Apim-Subscription-Key` 헤더에 **키 문자열 그대로** 전달합니다(일반 Bearer 토큰과 다름). JWT를 쓰는 시나리오라면 `Authorization: Bearer <token>` 헤더를 별도로 사용하세요. ([learn.microsoft.com][1])

### Agent 모드에서 실행

1. VS Code 좌측 **Tools** 아이콘에서 MCP 서버의 **툴 목록**을 확인.
2. 채팅에 프롬프트 입력 → 툴 실행 아이콘을 눌러 호출(예: `get information from order 2`). 결과는 선택한 툴 구성에 따라 텍스트로 반환됩니다. ([code.visualstudio.com][9])

---

## Additional Information: MCP 보안 가이드 & 팁

### 1. 인증/인가(Authorization) — MCP Auth 스펙 정렬

* **MCP Authorization**은 **OAuth 2.0 Protected Resource Metadata(PRM, RFC 9728)** 기반입니다. 서버는 PRM 문서를 통해 신뢰하는 \*\*Authorization Server(AS)\*\*를 광고하고, 클라이언트는 이를 따라 표준 플로우로 토큰을 획득합니다. APIM은 이 구조에서 **Auth 게이트웨이**로 동작하기 좋습니다. ([modelcontextprotocol.io][10], [The GitHub Blog][11], [learn.microsoft.com][12])
* **APIM + 원격 MCP 샘플**(Azure Functions, 최신 Auth 스펙 구현)을 참고하면 실전 적용이 수월합니다. ([learn.microsoft.com][12])

### 2. 키/토큰 취급

* **구독 키 노출 방지:** 인바운드에서 키를 검증하되, 백엔드로는 전달하지 않도록 `set-header` 정책으로 **구독 키 헤더 삭제**를 권장합니다. (예: `<set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />`) ([learn.microsoft.com][13], [ronaldbosma.github.io][14])
* **시크릿 관리:** APIM **Named Values** + **Key Vault 참조**를 사용해 비밀값을 관리(회전/권한 분리). ([learn.microsoft.com][15])

### 3. 전송/스트리밍

* MCP는 **스트리밍 우선**입니다. 정책에서 응답 본문을 버퍼링하지 않도록 주의하고, 진단 로깅의 응답 페이로드 바이트를 0으로 유지하세요. ([learn.microsoft.com][8])
* SSE/HTTP 전송을 혼용할 경우, **클라이언트·서버 전송 타입 일치**를 먼저 확인하세요. ([learn.microsoft.com][8])

### 4. AI 게이트웨이 정책

* **시맨틱 캐싱**, **토큰 리밋/모니터링** 정책으로 응답 지연과 비용을 절감하고, 남용을 사전에 차단합니다. ([learn.microsoft.com][4])

### 5. VS Code 통합 보안

* VS Code는 `MCP: Add Server`로 손쉽게 서버를 추가하고, 워크스페이스 `.vscode/mcp.json` 또는 전역 `settings.json`에 저장합니다. **신뢰 여부 확인 프롬프트**가 표시되니 서버 구성을 검토 후 승인하세요. ([code.visualstudio.com][9])

### 6. 엔터프라이즈 거버넌스

* **API Center**에 MCP 서버를 등록/검색하여 **엔터프라이즈 레지스트리**를 구축하면, 조직 내 서버 가시성과 수명주기 관리를 표준화할 수 있습니다. ([learn.microsoft.com][16])

---

## References
* **MCP 서버 개요 / 보안 액세스** (공식 Learn) ([learn.microsoft.com][3])
* **기존 MCP 서버 노출 및 정책 주의사항** (공식 Learn) ([learn.microsoft.com][8])
* **AI 게이트웨이 기능(시맨틱 캐싱/토큰 제어)** (공식 Learn) ([learn.microsoft.com][4])
* **VS Code에서 MCP 서버 사용** (공식 VS Code 문서) ([code.visualstudio.com][9])
* **APIM 확장(Visual Studio Code)** (마켓플레이스) ([Visual Studio Marketplace][17])
* **APIM 구독 키 헤더 규칙** (공식 Learn) ([learn.microsoft.com][1])
* **rate-limit-by-key 정책** (공식 Learn) ([learn.microsoft.com][2])
* **Named Values/Key Vault 연동** (공식 Learn) ([learn.microsoft.com][15])
* **Prompt Shields (Azure AI Content Safety)** (공식 Learn/블로그) ([learn.microsoft.com][18], [Microsoft Azure][19])
* **MCP 스펙 / Authorization(PRM)** (공식 MCP) ([modelcontextprotocol.io][20])
* **Remote MCP 샘플(Azure Functions + APIM)** (공식 샘플/Code Samples) ([learn.microsoft.com][12])
* **mcp-for-beginners(스타일/보안 모듈)** (공식 GitHub) ([GitHub][21])

---

> 💡 **실습 팁 요약**
>
> * 먼저 APIM에 API를 가져오고, 필요한 오퍼레이션만 **툴로 노출**합니다.
> * **Named Values + Key Vault**로 시크릿을 관리하고, 인바운드에서 구독 키를 검증 후 **백엔드로는 제거**합니다. ([learn.microsoft.com][15])
> * **rate-limit-by-key**로 클라이언트 IP/토큰/구독 단위 제한을 적용하고, 필요 시 **시맨틱 캐싱/토큰 정책**을 조합합니다. ([learn.microsoft.com][2])
> * VS Code \*\*`MCP: Add Server`\*\*로 서버 등록 후, **툴 패널**에서 바로 호출/검증합니다. ([code.visualstudio.com][9])
> * 스트리밍 정책/로깅 설정으로 **응답 버퍼링 금지**를 준수합니다. ([learn.microsoft.com][8])

---

### 부록 A — 흔한 구성 예시(헤더)

* **APIM 구독 키 사용:**
  `Ocp-Apim-Subscription-Key: <your-subscription-key>` (Bearer 접두사 **사용하지 않음**). ([learn.microsoft.com][1])
* **JWT/Bearer 사용:**
  `Authorization: Bearer <access_token>` (엔드투엔드 OAuth를 쓰는 시나리오). ([modelcontextprotocol.io][10])

### 부록 B — 시맨틱 캐싱/토큰 정책 어디서 보나요?

* APIM **GenAI 게이트웨이** 문서에서 정책/메트릭/한도 설정을 확인하세요(미리보기 포함). ([learn.microsoft.com][4])

---

[1]: https://learn.microsoft.com/en-us/azure/api-management/api-management-subscriptions?utm_source=chatgpt.com "Subscriptions in Azure API Management"
[2]: https://learn.microsoft.com/en-us/azure/api-management/rate-limit-by-key-policy?utm_source=chatgpt.com "Azure API Management policy reference - rate-limit-by-key"
[3]: https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview?utm_source=chatgpt.com "Overview of MCP servers in Azure API Management"
[4]: https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities?utm_source=chatgpt.com "AI gateway capabilities in Azure API Management"
[5]: https://techcommunity.microsoft.com/blog/integrationsonazureblog/expanding-genai-gateway-capabilities-in-azure-api-management/4214245?utm_source=chatgpt.com "Expanding GenAI Gateway Capabilities in Azure API ..."
[6]: https://learn.microsoft.com/en-us/azure/api-management/export-rest-mcp-server?utm_source=chatgpt.com "Expose REST API in API Management as MCP server"
[7]: https://learn.microsoft.com/en-us/azure/api-management/visual-studio-code-tutorial?utm_source=chatgpt.com "Tutorial - Import and manage APIs - Azure API ..."
[8]: https://learn.microsoft.com/en-us/azure/api-management/expose-existing-mcp-server?utm_source=chatgpt.com "Expose and govern existing MCP server - Azure"
[9]: https://code.visualstudio.com/docs/copilot/chat/mcp-servers?utm_source=chatgpt.com "Use MCP servers in VS Code"
[10]: https://modelcontextprotocol.io/specification/draft/basic/authorization?utm_source=chatgpt.com "Authorization"
[11]: https://github.blog/ai-and-ml/generative-ai/how-to-build-secure-and-scalable-remote-mcp-servers/?utm_source=chatgpt.com "How to build secure and scalable remote MCP servers"
[12]: https://learn.microsoft.com/en-us/samples/azure-samples/remote-mcp-apim-functions-python/remote-mcp-apim-functions-python/?utm_source=chatgpt.com "Remote MCP using Azure API Management - Code Samples"
[13]: https://learn.microsoft.com/en-us/azure/api-management/set-header-policy?utm_source=chatgpt.com "set-header - Azure API Management policy reference"
[14]: https://ronaldbosma.github.io/blog/2024/09/02/validate-api-management-policies-with-psrule/?utm_source=chatgpt.com "Validate API Management policies with PSRule | Ronald's Blog"
[15]: https://learn.microsoft.com/en-us/azure/api-management/api-management-howto-properties?utm_source=chatgpt.com "How to use named values in Azure API Management policies"
[16]: https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server?utm_source=chatgpt.com "Inventory and Discover MCP Servers in Your API Center"
[17]: https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-apimanagement&utm_source=chatgpt.com "Azure API Management Extension for Visual Studio Code"
[18]: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection?utm_source=chatgpt.com "Prompt Shields in Azure AI Content Safety"
[19]: https://azure.microsoft.com/en-us/blog/enhance-ai-security-with-azure-prompt-shields-and-azure-ai-content-safety/?utm_source=chatgpt.com "Enhance AI security with Azure Prompt Shields and ..."
[20]: https://modelcontextprotocol.io/specification/2025-03-26?utm_source=chatgpt.com "Specification"
[21]: https://github.com/microsoft/mcp-for-beginners "GitHub - microsoft/mcp-for-beginners: This open-source curriculum introduces the fundamentals of Model Context Protocol (MCP) through real-world, cross-language examples in .NET, Java, TypeScript, JavaScript, Rust and Python. Designed for developers, it focuses on practical techniques for building modular, scalable, and secure AI workflows from session setup to service orchestration."
