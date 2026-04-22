---
title: Cognitive Debt with AI-generated Code
subtitle: An old problem at light speed
slug: cognitive-debt
date: 2026-04-22
excerpt: Cognitive debt is an old problem wearing new clothes. Agentic coding just accelerates that phenomenon to light speed.
---

Cognitive debt is an old problem wearing new clothes. If you are reading this, you have seen it before – a senior engineer leaves, and suddenly the team is scared to touch half the codebase because nobody else understood *why* it worked the way it did. Things break, and no one knows where to look. That was always a risk. Agentic coding just accelerates that phenomenon to light speed.

The term was coined by Margaret Storey, a computer science professor who's been studying developer productivity for over two decades. There's also a [MIT paper](https://www.media.mit.edu/publications/your-brain-on-chatgpt/) that frames it more broadly – the accumulated cognitive cost of outsourcing your thinking to LLMs. Consistent underperformance at neural, linguistic, and behavioural levels in LLM-heavy groups compared to non-users. Polemically shortened: the cost of becoming more stupid through AI usage.

But in software, cognitive debt isn't about individual intelligence. It's about *shared theory* or the collective understanding your team has about how a system works, why decisions were made, and what the boundaries are. Technical debt in the same vein is not some magical, autonomous deterioration of code - it's also the collective human factor, the accumulation of architectural decisions over time that make maintenance harder and harder. Cognitive debt is the same mechanic, but instead of the code degrading, your shared understanding of it does. Then production is down and your team is staring at the code like it's some ancient Mesopotamian stonewall.

The dangerous thing is that you might recognise it as a problem when it's already too late to cheaply reverse. Your velocity metrics look fantastic. You shipped (insert fantastic number of choice)% more features this quarter, all on AI-steroids. But when an incident hits an AI-written module and the resolution takes four times longer because nobody can trace the logic – that's your interest payment on cognitive debt. And more API usage billed for your GitHub Copilot.

So what do you actually do about it?

The natural cure might simply be the end of subsidised token use – I swear, one of these days I will write that blog post about the real pricing of AI-compute, but today is not the day. Maybe it will just stay a meme to hide in every single blog post I write. But running out of a session limit with your Claude Max subscription has the same effect: slowing down. And slowing down is, annoyingly, the point.

The practices to prevent cognitive debt already exist. TDD, pair programming, refactoring, rigorous code review. Nothing new. Code review in particular was never really about catching bugs – it was the primary mechanism for knowledge transfer. Juniors learned architecture by reading senior PRs. Seniors maintained context by reviewing everything. AI bypasses that entire loop. The code shows up, it works, tests pass, it gets merged. Nobody learned anything. Nobody built context.

You could spin up agents to review and document for you – but they cannot retain the shared theory your team needs, the *why* your code works a certain way. They can generate decision records, sure, but those still need human eyes to become shared understanding. As long as agents can't hold that memory for your team, the rule is straightforward: at least one team member must be able to explain any AI-generated code change before it ships. Not read it. *Explain* it. Can I walk a teammate through every line? Do I understand why this approach was chosen over alternatives? Could I debug this at 3 a.m. without reprompting? If the answer to any of those is no, it doesn't merge.

I am a huge proponent of velocity over everything...it's literally in the name of the blog. But speed without understanding is not velocity. You will be sprinting on borrowed time.

---
**Further reading:**
- [Margaret Storey – Cognitive Debt](https://margaretstorey.com/blog/2026/02/09/cognitive-debt/)
- [Margaret Storey – Cognitive Debt Revisited](https://margaretstorey.com/blog/2026/02/18/cognitive-debt-revisited/)
- [Kosmyna et al. – "Your Brain on ChatGPT: Accumulation of Cognitive Debt When Using an AI Assistant for Essay Writing Task"](https://www.media.mit.edu/publications/your-brain-on-chatgpt/)
