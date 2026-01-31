
import asyncio
from langchain_core.messages import AIMessage, HumanMessage
from graph import create_agent
from mcp_manager import mcp_manager

graph = create_agent().compile()


# ============================================================================
# CLI
# ============================================================================

async def run_agent(message: str):
    print(f"\n{'='*60}\n🎯 Task: {message}\n{'='*60}")
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content=message)]})
        print(f"\n{'='*60}\n📤 RESULT:\n{'='*60}")
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                print(msg.content)
                break
        return result
    finally:
        await mcp_manager.cleanup()


def main():
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "明天北京天气如何"
    asyncio.run(run_agent(query))


if __name__ == "__main__":
    main()