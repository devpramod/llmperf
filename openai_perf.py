from openai import OpenAI
from timeit import default_timer as timer

# Add these lines at the beginning of the file
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

def ttft_measurer(prompt, args):
    model = args.model
    def single_request():
        start = timer()
        completion = client.completions.create(
            model=model,
                        echo=False,
                        prompt=prompt,
                        max_tokens=1,
                        temperature=0,
                        n=1,
                        stream=True,
            )
        
        for _ in completion:
            pass
        return timer() - start
    return single_request

def tpot_measurer(prompt, args):
    model = args.model
    async def single_request():
        start = timer()
        completion = client.completions.create(
            model=model,
                        echo=False,
                        prompt=prompt,
                        max_tokens=args.output_tokens,
                        temperature=0,
                        n=1,
                        stream=True,
            )

        i = 0
        for _ in completion:
            if i == 0:
                start = timer()
            i += 1
        return (timer() - start) / (i - 1)
    return single_request

def rate_throughput_measurer(prompt, args):
    model = args.model
    async def single_request():
        completion = await client.completions.create(
            model=model,
                        echo=False,
                        prompt=prompt,
                        max_tokens=args.output_tokens,
                        temperature=0,
                        n=1,
                        stream=True,
            )
        async for _ in completion:
            pass
        return args.output_tokens
    return single_request

def sample_rate_throughput_measurer(args):
    model = args.model
    async def single_request(sample):
        completion = await client.completions.create(
            model=model,
                        echo=False,
                        prompt=sample["prompt"],
                        max_tokens=sample["output_len"],
                        temperature=0,
                        n=1,
                        stream=True,
            )
        async for _ in completion:
            pass
        return sample["output_len"]
    return single_request

def sample_output_rate_throughput_measurer(args):
    model = args.model
    async def single_request(sample):
        completion = await client.completions.create(
            model=model,
                        echo=False,
                        prompt=sample["prompt"],
                        temperature=1,
                        max_tokens=2048,
                        top_k=15,
                        n=1,
                        stream=False,
            )
        return completion.usage.completion_tokens
    return single_request


def static_batch_measurer(prompt, args):
    client = OpenAI(
        api_key=args.api_key,
        base_url=args.api_base
    )
    
    def single_request():
        start = timer()
        responses = []
        for _ in range(args.batch_size):
            response = client.completions.create(
                model=args.model,
                prompt=prompt,
                max_tokens=args.output_tokens,
                temperature=0.0,
                stream=False
            )
            responses.append(response)
        
        end = timer()
        total_time = end - start
        total_tokens = sum(len(r.choices[0].text.split()) for r in responses)
        return total_tokens / total_time  # tokens per second
    
    return single_request