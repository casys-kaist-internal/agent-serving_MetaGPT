#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import re

import typer
from human_eval.data import read_problems, write_jsonl
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from metagpt.actions import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger


logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

# --- Custom Action & Role for HumanEval (based on the example) ---
class GenerateHumanEvalCompletion(Action):

    PROMPT_TEMPLATE: str = (
        "You are an AI that only responds with Python code, NOT ENGLISH. You will be given a function signature and its docstring by the user. Write your full implementation"
        "```python\n{instruction}\n```."
    )

    name: str = "GenerateHumanEvalCompletion"

    async def run(self, instruction: str) -> str:
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        rsp = await self._aask(prompt)
        return self.parse_code(rsp)

    @staticmethod
    def parse_code(rsp: str) -> str:
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text.strip()


class HumanEvalCoder(Role):
    name: str = "HumanEvalCoder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateHumanEvalCompletion])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo 
        prompt_message = self.get_memories(k=1)[0]
        code_text = await todo.run(prompt_message.content)
        return Message(content=code_text, role=self.profile, cause_by=type(todo))


async def generate_one_completion(prompt: str) -> str:
    try:
        role = HumanEvalCoder()
        result_message = await role.run(prompt)
        return result_message.content
    except Exception as e:
        logger.error(f"\nError during generation for prompt '{prompt}': {e}")
        return ""

async def main(
    output_file: str = typer.Option("samples.jsonl", help="The path to save the generated samples."),
    limit: int = typer.Option(0, help="Limit the number of problems to process for testing. 0 means all."),
    num_samples_per_task: int = typer.Option(1, "--num-samples", help="Number of samples to generate per task."),
):
    logger.info("Starting HumanEval code generation with a custom MetaGPT Coder...")
    
    problems = read_problems()
    tasks = list(problems.items())

    if limit > 0:
        tasks = tasks[:limit]

    samples = []

    for i in range(num_samples_per_task):
        logger.info(f"\n--- Starting Generation Round {i + 1} of {num_samples_per_task} ---")

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
        ) as progress:
            task_progress = progress.add_task("[cyan]Generating completions", total=len(tasks))

            for task_id, problem in tasks:
                completion = await generate_one_completion(problem["prompt"])
                
                if completion:
                    samples.append(dict(task_id=task_id, completion=completion))
                
                progress.update(task_progress, advance=1)

    write_jsonl(output_file, samples)
    logger.info(f"\n✅ Generation complete! {len(samples)} samples saved to '{output_file}'.")


if __name__ == "__main__":
    def cli_wrapper(
        output_file: str = "data/samples.jsonl",
        limit: int = 0,
        num_samples_per_task: int = 1,
    ):
        asyncio.run(main(output_file, limit, num_samples_per_task))

    typer.run(cli_wrapper)