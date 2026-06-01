# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Binh Huy
- **Team**: Team C-6
- **Date**: 01-06-2026

---

## I. Technical Contribution (15 Points)

For this lab project, my main job was to build the core brain of our AI assistant. I wrote the code that decides when to use the simple chatbot and when to activate the smart ReAct agent, and I also created the diagrams that explain how all these pieces connect and work together.

**What I actually worked on:**

- **`src/agent/hybrid_flow.py`**: This is where the main helper class (`HybridBookAssistant`) lives, which controls the entire experience. I wanted our system to be smart but also fast. To achieve this, I set it up so that it first checks our local list of books. If there is a match, it answers right away (which takes almost 0ms). If it's a miss, it starts the slow but smart ReAct loop. In this file, I also wrote a safety check to stop the LLM from making up its own tool results (hallucinating the `Observation:` lines) and added a filter to make sure that when the agent recommends similar books, it doesn't just list the book we originally asked about. I also made sure the agent doesn't get stuck in an infinite loop by stopping it after a maximum of 10 steps.

- **`src/agent/agent.py`**: I created the basic structure of the ReAct agent. I wrote the system prompt that teaches the model how to follow the Thought, Action, and Observation loop. I wanted to keep this file simple and easy to understand so that my teammates could build their tools on top of it without getting confused by the complex agent code.

- **`report/group_report/GROUP_REPORT_TEAM_6.md`**: I drafted our full group report. I explained how our system works, how we improved our tools from the first version to the second version, and how we solved several annoying bugs. 

- **`report/group_report/react_workflow.png`**: I spent a lot of time drawing our system flowchart. It maps out the entire flow of the program, showing exactly where the chatbot stops and where the agent takes over. I also added actual time and token measurements from our test runs using GPT-4o and Gemini so we could clearly see the performance difference.

All my code is written to be clean and modular. Every single method has just one job, and we log structured events like `TOOL_CALL`, `TOOL_RESULT`, `LLM_METRIC`, and `AGENT_THOUGHT_ACTION` at every step so we can track exactly what the agent is doing in real-time. I also made sure we can easily switch between OpenAI, Gemini, or local models just by changing one line in the `.env` file.

---

## II. Debugging Case Study (10 Points)

**The Problem**: One very annoying bug I ran into while writing `hybrid_flow.py` was that the agent kept "cheating". Instead of asking the computer to run the Wikipedia search or OpenLibrary search, the LLM would just write down its own fake search results inside its text response! It would print out its `Thought`, its `Action`, and then immediately write `Observation: [some made-up book information]` all in one go without actually running our Python functions.

**Log Evidence**: While looking at the log file (`tests/logs/2026-06-01.log`) from a test run, I saw that the agent wrote a thought about finding a book, and then the very next line in the log showed the agent reasoning with a list of books as if it had already searched it. But when I looked closely at the telemetry events, there was no `TOOL_CALL` or `TOOL_RESULT` logged in between those steps. The model had just skipped the middle step and fabricated the answer.

**Root Cause**: The system prompt I wrote taught the model the format: `Thought → Action → Observation`. But because these language models are trained to complete text patterns, it didn't want to stop after writing `Action`. It just kept writing and completed the `Observation` part itself.

**How I Diagnosed It**: I compared a correct run and a failing run side-by-side in the log file. In the correct run, every `Action` line was always followed by a `TOOL_CALL` event. In the failing run, the `TOOL_CALL` was completely missing, which was a clear indicator that the LLM was hallucinating the observation.

**How I Fixed It**: I did two things. First, in the Python code, I wrote a line that looks at what the LLM generated and immediately cuts off anything starting from the word "Observation:". This way, even if the model tries to cheat and write the observation, our code chops it off and forces it to wait. Second, I updated the system prompt to explicitly tell the model: "Write the Action and then STOP. Do not write the Observation." I also put a couple of few-shot examples in the prompt to show it how to wait correctly.

**The Result**: Once I added the code cutoff and the updated prompt, I ran the tests again and checked the logs. The fake observations disappeared completely, and the model correctly waited for the tool to execute every single time.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**What I learned about the Thought block**: When I first heard about ReAct agents, I thought the `Thought:` step would make the agent much smarter. But as I watched the logs, I realized that writing down a thought doesn't actually guarantee that the agent will follow it. Sometimes, the agent writes a really good, logical plan in its `Thought`, but then immediately makes a silly mistake in the next step. For example, during one test, the model wrote: "I need to search Wikipedia to find a summary of the book." But right after that, instead of choosing the Wikipedia tool, it just generated the final answer using its own memory. It looked like it was planning carefully, but it was still just guessing. By contrast, our simple chatbot is much more reliable because we force it to only use the local database, meaning it doesn't have the freedom to make things up.

**When the Agent is worse than the Chatbot**: Through our test cases, I saw that the Agent can be really wasteful. If a user asks about a book we already have in our database (like "Chi Pheo"), the chatbot answers in less than a second for free. But the Agent will activate its loop, make 4 slow calls to Wikipedia and OpenLibrary over the internet, and take 10 seconds just to say the same thing. Also, if the internet is slow or if Wikipedia blocks our requests (like when we get a 429 rate limit error), the agent just burns through tokens and takes forever before finally giving up. And for simple things like saying "Hello", the agent is just a waste of time. That's why I'm really glad we put the chatbot database check at the very beginning of the code, so we don't start the slow agent loop unless we absolutely have to.

**How Observations ground the Agent**: The coolest part of the ReAct agent is how it uses the observations it gets from the tools. Every time a tool runs, we take the result (like the subject of a book from OpenLibrary) and feed it back into the prompt for the next step. This is what keeps the agent "grounded" in reality. If the tool returns "Fantasy", the model is forced to recommend fantasy books in the next step, rather than making up some random category. This is the big difference between the chatbot and the agent: the chatbot only knows what's inside its head or in our local file, but the agent adapts and learns new facts by interacting with the tools in real-time.

---

## IV. Future Improvements (5 Points)

**Making it faster**: Right now, our agent is pretty slow, taking anywhere from 9 to 30+ seconds. This is because it does everything in a straight line: it searches Wikipedia, waits, searches the book, waits, gets the subjects, and so on. If I were to write this again, I would try to make these searches run at the same time (using Python's `asyncio`). For example, we could search Wikipedia and OpenLibrary at the exact same moment and save a lot of seconds. Also, instead of a simple hard-coded list of 10 books in our chatbot database, we should use a vector database like ChromaDB. This would allow the chatbot to search through thousands of books very fast using semantic search, so we wouldn't have to trigger the slow agent loop as often.

**Making it safer**: Our current system has basic safety checks (like trying 3 times if the internet fails), but it can still be easily fooled. If someone asks a non-book question (like a song or a movie), the agent will waste time searching OpenLibrary before realizing it's not a book. I think we should add a quick check at the very beginning to see if the user is actually asking about a book before we do anything. We could also have another "checker" LLM that watches the agent to make sure it doesn't do anything stupid, like calling the exact same tool twice in a row.

**Upgrading the structure**: The `while` loop we used to run the agent is simple, but it's very rigid. If a search fails, the agent doesn't really know how to recover or try a different path. If we migrated the code to a framework like LangGraph, we could build a much smarter flow. For example, if a Vietnamese Wikipedia search returns nothing, the agent could automatically branch off and try searching in English. And if we want to expand this to other topics besides books, we could have one "coordinator" agent that forwards the question to specialized "expert" agents, while still keeping our logs and tracking system in place.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
