# 全新 LangGraph 项目

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

该模板演示了一个使用 [LangGraph](https://github.com/langchain-ai/langgraph) 实现的简单应用，旨在展示如何开始使用 [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/#langgraph-server) 以及 [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/)（一个可视化调试 IDE）。

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

定义在 `src/agent/graph.py` 中的核心逻辑展示了一个单步应用：它会返回一个固定字符串以及提供的配置。

你可以扩展这张图，以编排更复杂的智能体工作流，并在 LangGraph Studio 中进行可视化和调试。

## 快速开始

1. 安装依赖，并安装用于运行服务端的 [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/)。

```bash
cd path/to/your/app
pip install -e . "langgraph-cli[inmem]"
```

2. （可选）按需自定义代码和项目。如果需要使用密钥，请创建 `.env` 文件。

```bash
cp .env.example .env
```

如果你想启用 LangSmith tracing，请将你的 LangSmith API key 添加到 `.env` 文件中。

```text
# .env
LANGSMITH_API_KEY=lsv2...
```

3. 启动 LangGraph Server。

```shell
langgraph dev
```

有关 LangGraph Server 快速开始的更多信息，[请见这里](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)。

## 如何自定义

1. **定义运行时上下文**：修改 `graph.py` 文件中的 `Context` 类，以暴露你希望为每个 assistant 配置的参数。例如，在聊天机器人应用中，你可能希望定义动态 system prompt 或要使用的 LLM。有关 LangGraph 中运行时上下文的更多信息，[请见这里](https://langchain-ai.github.io/langgraph/agents/context/?h=context#static-runtime-context)。

2. **扩展图**：应用的核心逻辑定义在 [graph.py](./src/agent/graph.py) 中。你可以修改该文件以添加新的节点、边，或更改信息流。

## 开发

在 LangGraph Studio 中迭代你的图时，你可以编辑过去的状态，并从先前状态重新运行应用来调试特定节点。本地改动会通过热重载自动生效。

后续请求会沿用同一条线程。你可以使用右上角的 `+` 按钮创建一条全新线程，从而清空之前的历史记录。

如需更高级的功能和示例，请参考 [LangGraph 文档](https://langchain-ai.github.io/langgraph/)。这些资源可以帮助你将该模板适配到你的具体场景，并构建更复杂的对话智能体。

LangGraph Studio 还集成了 [LangSmith](https://smith.langchain.com/)，用于更深入的追踪以及与团队成员协作，从而帮助你分析和优化聊天机器人的性能。
