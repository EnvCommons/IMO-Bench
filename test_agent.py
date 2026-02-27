import json
import asyncio
import os

from openai import AsyncOpenAI
from openreward import AsyncOpenReward

MODEL_NAME = "gpt-5.2"

VARIANTS = [
    "IMOBenchAnswerBench",
    "IMOBenchGradingBench",
    "IMOBenchProofBench",
]


async def run_variant(or_client, oai_client, env_name, variant, secrets, num_tasks=1):
    print(f"\n{'='*60}")
    print(f"  {variant}")
    print(f"{'='*60}")

    environment = or_client.environments.get(name=env_name, base_url="http://localhost:8080", variant=variant)
    tasks = await environment.list_tasks(split="all")
    tools = await environment.list_tools(format="openai")

    print(f"  Tasks available: {len(tasks)}")
    print(f"  Tools: {len(tools)}")

    for idx, task in enumerate(tasks[:num_tasks]):
        print(f"\n  --- Task {idx + 1}/{min(num_tasks, len(tasks))} ---")

        async with environment.session(task=task, secrets=secrets) as session:
            prompt = await session.get_prompt()
            input_list = [{"role": "user", "content": prompt[0].text}]
            finished = False

            print(f"  Prompt: {prompt[0].text[:200]}...")

            iteration = 0
            max_iterations = 10

            while not finished and iteration < max_iterations:
                iteration += 1

                response = await oai_client.responses.create(
                    model=MODEL_NAME,
                    tools=tools,
                    input=input_list,
                )

                input_list += response.output

                for item in response.output:
                    if item.type == "function_call":
                        tool_result = await session.call_tool(
                            item.name,
                            json.loads(str(item.arguments)),
                        )

                        reward = tool_result.reward
                        finished = tool_result.finished

                        input_list.append({
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": tool_result.blocks[0].text,
                        })

                        print(f"  Tool: {item.name} | Reward: {reward}")
                        print(f"  Output: {tool_result.blocks[0].text[:100]}")

                        if finished:
                            print(f"  ✓ Completed with reward: {reward}")
                            break

                if not any(i.type == "function_call" for i in response.output):
                    break

            if iteration >= max_iterations:
                print(f"  ✗ Reached max iterations ({max_iterations})")


async def main():
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    or_client = AsyncOpenReward()
    oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    ENV_NAME = "YourOrg/imobench"  # Update with actual org

    secrets = {"openai_api_key": OPENAI_API_KEY}
    if GEMINI_API_KEY:
        secrets["gemini_api_key"] = GEMINI_API_KEY

    for variant in VARIANTS:
        await run_variant(or_client, oai_client, ENV_NAME, variant, secrets)


if __name__ == "__main__":
    asyncio.run(main())
