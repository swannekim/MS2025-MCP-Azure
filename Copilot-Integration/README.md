github copilot 을 mcp client로 사용하기

1. vs code에서 mcp configuration 파일(mcp.json)에서 install 된 mcp server 확인
![open mcp config file](../img/mcp-config-open.png)

2. github copilot chat toggle open -> agent 모드 설정
![mcp config and copilot toggle](../img/mcp-config-copilot.png)

---

mcp 서버사용 실습

mcp.json 에서 run server -> running 확인 -> tool 128개 이하 되도록 관련 / 사용할 tool만 선택

1. playwright mcp
(playwright은 뭐하는 mcp 서버인지 간단 설명)

![run playwright & chat](../img/mcp-playwright-1.png)
chat 예시: I live in Manchester, UK. Go to https://tfl.gov.uk/ and help me plan travel from Manchester Piccadilly Station to Knightsbridge Station at London. I am going to travel on Friday, 15 August. I am excited to travel to London!

![playwright chat example](../img/mcp-playwright-2.png)
![screenshot of journey results provided by playwright](../img/playwright-mcp/tfl-journey-results-manchester-knightsbridge.png)

2. azure mcp
https://github.com/Azure/azure-mcp

chat 예시: list up my azure resources // can you provide some information of my azure subscription?
![chats asking for subscription & resources info](../img/mcp-azure-1.png)

chat 예시: What resource groups, or resources of my subscription are leading to a high cost? I need some management. // can you help me deploy models at azure ai foundry?
![chats for cost management & deploy models](../img/mcp-azure-2.png)

3. azure ai foundry mcp
https://github.com/azure-ai-foundry/mcp-foundry
일부 기능 사용하기 위해서는 .env 설정 필요 (.env.example 참조. 상단 github에 나와있음)
![chat result for how to fill .env](../img/mcp-foundry-env.png)

chat 예시: What models are good for reasoning? Show me some examples in two buckets, one for large models and one for small models. Explain why. // from these, what can i currently use if i am in the korea central region? // i need specific deployment instructions and your help in deploying Llama 4 Scout 17B
![chat result for model recommendation](../img/mcp-foundry-1.png)
![chat result for deployment instructions](../img/mcp-foundry-2.png)