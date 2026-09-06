# PM Operating Manual
**Chris Bell | March 2026 — Working Draft**

---

This document covers how I think PMs should operate - the craft, the cross-functional relationships, and the mechanics of building and delivering product. It goes deeper than the "Working With Me" doc. Use it as a reference, not a checklist.

---

## Understanding Customers

### Buyers, Users, and the Gap Between Them

The most important distinction in understanding customers is the difference between the buyer and the user. In enterprise settings especially, these are often different people with different pressures, different vocabularies, and different definitions of success.

Buyers are often executives. They care about outcomes, risk, cost, and whether the solution fits their organization's direction. They are not always the people who use the product every day.

Users live with the product. They care about whether it fits into their workflow, whether it is fast and reliable, and whether it makes their day easier or harder. They are often the ones who can tell you where your product actually breaks down.

Good customer work means engaging both. It means reading behind what someone asks for to understand the underlying pressure. It means pattern-matching across many customer conversations to see what problems are systemic versus idiosyncratic.

One of the harder things to learn: buyer and user needs sometimes point in opposite directions. This tension is becoming more common in the AI era, where automation that serves the buyer's efficiency goals can directly undermine the user's sense of control or competence. See it clearly rather than pretend it does not exist.

### Digging for What Is Actually Hard

Getting customers to tell you what is actually hard takes discipline. People default to the problems that are clearly in scope for your product. But some of the most important things you can learn live beyond that boundary - in the adjacent workflow, the upstream decision, the process they handle manually because nothing automates it. You have to dig, and you have to make it safe for them to tell you about problems you might not be able to solve.

### Finding the Critical Few

One of the most important things to figure out - and you cannot do it by asking directly - is what 15 to 20 percent of your product is genuinely mission-critical to each customer. Ask them and they will tell you it is all important. It is not. Mission-critical means: if this broke or went away, there would be a real business problem with real consequences. Everything else is negotiable.

You have to triangulate this through behavior, support escalations, renewal conversations, and what customers actually complain about when things go wrong. The answer is often surprising. It is rarely the features the roadmap has been organized around. And it frequently includes things that are not features at all - trust, stability, a particular workflow that is deeply embedded in how their team operates. Understanding this is what separates teams that protect the right things when resources get tight from teams that optimize for the wrong ones.

### Picking the Right Customers

Not all customers are worth the same. Not all revenue is worth the same. This sounds obvious and it is consistently under-applied.

A PM should be able to identify the profile of a high-value customer - one whose problems are squarely in the product's strength zone, who will use the product as intended, who will generate meaningful signal about what to build next, and who, if they are successful, will become a credible reference that others in the market pay attention to. A marquee customer who succeeds publicly changes the sales motion. That profile should inform which deals the team engages with deeply, which references get prioritized, and which inbound interest is worth pursuing.

It also means being able to identify bad fits - customers whose needs require so much customization that the work generates no reusable value, customers in segments the product was not built for, customers whose success criteria conflict with the direction the product is heading. Saying no to a customer is hard. Signing the wrong customer and then spending eighteen months trying to make them successful is much harder.

This matters most with pilots. A pilot with the wrong customer is a trap. Even if it succeeds on paper, it generates a reference and creates an expectation in a segment that may not be strategic. Before agreeing to a pilot, the question is not just "can we make this work" - it is "if this succeeds, do we want the customer it produces?"

---

## Developing Ideas

### Crayon-Level Thinking

When developing a new idea - a business case, a design concept, a feature - start at the lowest fidelity that still communicates the idea. Think of a four-year-old drawing a house with a crayon. The fidelity is low. The proportions are off. But you can tell what it is supposed to be - and more importantly, you can tell what it is not.

The value of starting rough is that low fidelity invites input. When something looks finished, people react to what is there. When something looks like a sketch, people tell you what is missing. Nobody falls in love with a crayon drawing, which means you can change it without anyone feeling like their investment got thrown away.

The failure mode is over-investing early. A PM who builds a polished spec before the idea has been stress-tested has done a lot of work that is now hard to throw away. That attachment - to the investment, not the idea - is one of the main reasons products get built that should not have been.

### The Double Diamond

The process of developing an idea is not a straight line. Good product thinking follows a rhythm of diverging and converging - and it does this twice.

The first diamond is about the problem. You start by opening up - exploring the problem space broadly, talking to customers, questioning your assumptions about what is actually wrong and who it actually affects. Then you converge on a clear and specific problem definition. Most teams rush this phase. The second diamond is about the solution. You open up again - generating options, sketching alternatives, resisting the pull toward the first idea that seems to work. Then you converge on what to build and test.

The failure mode is treating this as more linear than it is. Teams that skip the first diamond converge on the wrong problem efficiently. Teams that never fully converge on either diamond produce a lot of interesting thinking and not much that ships. Part of the PM's job is reading where the team is in the process and steering accordingly - opening up when the thinking has gotten too narrow too fast, and closing down when the team needs a decision.

### Hypothesis Testing

The discipline that connects divergent thinking to real decisions is the scientific method, applied to product.

Work through it in this order:

**Theory.** What do you believe about the world? What is true about your customers, their problems, or the market that makes your idea worth pursuing? Be explicit about your assumptions - they are what you are testing.

**Hypothesis.** A specific, falsifiable statement that follows from your theory. "Customers will find this valuable" is not a hypothesis. "Customers in segment X who currently solve this problem with spreadsheets will pay to automate it, and we will know this if N percent of pilot users complete the workflow without prompting within their first two sessions" is a hypothesis you can actually test.

**Experiment.** What is the minimum you need to build or do to test this hypothesis? The experiment should be designed to produce signal on the hypothesis - not to validate the product generally, and not to produce a polished demo. Design the test, not the product.

**Observation.** What did you actually see? Separate observation from interpretation at this stage. What happened, specifically?

**Conclusion.** What does the observation tell you about the hypothesis? What do you now believe that you did not before? And critically - what do you do next? A positive result is not the end of the loop; it is a signal to invest more and test the next hypothesis. A negative result is not a failure; it is information you needed.

Being explicit about the success signal before you run the test matters. Teams that define success after the fact have a strong tendency to find it.

---

## Product Strategy

A product strategy is not a good idea dressed up in slides. It is a structured argument for where to compete, why you will win there, and what you need to build to do it. We typically do not update this more than once a year, but it should be live enough that people can actually use it to make decisions.

A complete product strategy covers:

**Target market.** Who specifically you are building for - not just a demographic but a clearly defined Ideal Customer Profile (ICP) and a credible read on market size. I am not a fan of TAM/SAM/SOM as a framework - it too often produces numbers that feel rigorous but are assembled from assumptions. A sharper question is: how many customers with this problem exist, how many can we realistically reach, and what are they currently paying to solve it?

**The core problem.** What you are solving and why it is genuinely valuable to solve. Not "the market needs a better solution" but a specific articulation of the pain, who feels it most acutely, and why now.

**Competitive landscape.** What the alternatives are - including free ones. "Live with the problem," pen and paper, and spreadsheets are always on this list. So is doing nothing. If you cannot articulate why someone would choose your product over those options, you do not have a strategy yet.

**Value proposition and differentiators.** Why your target market will pay you to solve this relative to every alternative on that list. This should be specific enough to be testable.

**Business goals.** Are you trying to expand into a new market, sell more to existing customers, reduce operating costs, build a moat for something else? The goals shape what success looks like and which tradeoffs are acceptable. A strategy that does not connect to explicit business goals will eventually get cut when resources get tight.

A good product strategy flows from company goals downward to team and product. If you cannot draw that line, either the strategy is wrong or the company goals are unclear - and either way, that is worth surfacing.

---

## Written Artifacts of Product Work

PMs communicate through documents. The quality of your documents reflects the quality of your thinking, and it shapes whether the people around you can engage with your ideas effectively. There is no single right format, but there are a few artifacts that most product work requires.

### Business Case

The business case answers one question: is this a good idea worth spending more time on? The reader should finish it knowing whether they agree.

A business case covers the product strategy (condensed), a rough financial picture (what will it cost to build and to run, what can we realistically sell in what timeframe, and what other sources of value it creates), and a clear statement of what you are asking the business to invest. The critical word is "rough." A business case is not asking for a greenlight to build - it is asking for a greenlight to learn. Because you are not asking for much, do not over-invest in producing the document. A tight, well-reasoned two-pager beats a polished ten-pager that took three weeks to write. The goal is alignment on the goals and the scale of investment before you go further.

### Product Brief

The product brief is the meat in the sandwich. The product strategy is the top slice - the company-level direction, the target market, the big bets. The PRDs are the bottom slice - the specific features and requirements your team is building. The product brief is what goes in between, and without it the whole thing falls apart.

It takes the overall product strategy and focuses it on your specific piece of the business, translating company-level direction into something your team can actually operate from. It articulates where you want to take that piece of the business over the next period, and why.

Review it quarterly (or at whatever cadence matches the rhythm of your business) to make sure it reflects your latest thinking and what you have learned. A well-written and actively maintained product brief does something important beyond alignment: it makes PRD decisions easier. When you are deciding whether to pursue a feature, a well-maintained brief should be able to tell you whether it belongs - or does not.

### PRD (Product Requirements Document)

The PRD is the user stories and requirements for the specific feature or product you are building. Three things it needs to accomplish:

First, it should explain narratively what you are trying to solve for the customer and the business - the strategy and the why. Anyone reading it should understand not just what you are building but what problem it is in service of.

Second, it should be clear enough that the business and the development team know exactly what you want to build. This includes the user experience, service level indicators (what gets measured to know this is functioning correctly), and ideally the service level objectives (the actual targets). If you cannot write this clearly, you are not ready to build.

Third, your partners - engineering, design, data - should be able to read it and tell you whether the thing you have described is the best way to achieve the goals you have laid out. If the spec does not invite that conversation, it is too finished.

AI is useful here. Use it to structure a draft, check your logic, surface requirements you have not thought of yet, and pressure-test whether the document actually answers the questions above.

---

## Prioritization

Prioritization is part art, part science. At the highest level, you want to make bets on investments with the highest return and the lowest risk. I dislike frameworks like RICE - they are too easily gamed, the inputs are subjective enough that motivated reasoning can produce almost any answer, and they tend to optimize for things that are easy to score rather than things that actually matter. Use judgment, be explicit about your reasoning, and be willing to defend it.

Two lenses help structure that judgment:

**Return.** How big, important, and valuable is the problem you are tackling? A large, painful problem felt by many customers in your target segment is a better bet than a small one felt by few, even if the small one is easier to solve.

**Risk.** How confident are you that you can solve it, and how have you structured the work to find out cheaply? Great projects are not just high-return - they are also structured to reduce risk early. MVPs, hypothesis tests, and clear go/no-go criteria at each stage are not project management overhead; they are how you avoid large bets on unvalidated assumptions.

Even with both lenses you could stack-rank a list and work down it. But that still leaves the harder question unanswered: what does the market actually expect from you, and when?

That is where the art lives. You need to understand what your customers and the market have come to expect from your product - not just what they ask for, but what they would notice if it were missing or late. "The market" is not a monolith. Who is asking for something? How many of them? How long have they been asking? What is the cost - in trust, in churn, in competitive position - of saying "not now"? These questions do not have formula answers. You should have a point of view on them. I will have one too. We will not always agree, and that tension is useful.

---

## Working Across the Organization

### Engineering Partnership

The PM-engineering relationship is not a client-vendor relationship. It is a partnership, and the frame I try to establish is: your problems are my problems, and my problems are your problems.

Understand how the product works, at least at the level of boxes and arrows. Not to second-guess engineers, but because a PM who does not understand the technical architecture cannot anticipate how engineering decisions will affect customers. The relationship only works if engineers trust that you are engaging in good faith with the complexity of what they are building.

Engineering should not just build what PM asks for - and I do not want them to. I want engineering partners who push back when a request does not make sense, who hold the PM accountable for actually representing the customer and the business, and who bring their own perspective to the problem. A PM who has earned that kind of relationship with their engineering counterparts is building something real.

Bring concepts to engineering partners early - intentionally fuzzy, not fully formed. The goal is to invite them into the thinking, not present them with a finished spec. The best product decisions come out of a PM and an engineer looking at a half-formed idea together and figuring out what it should actually be.

Engineering investments - reliability, performance, technical debt reduction - often lose to customer features in the short run, and organizations pay for that repeatedly. Part of the PM's job is making sure those investments get a fair hearing and that their value is legible to the people making prioritization decisions.

### Sales and Go-to-Market Relationship

Sales and product are not naturally aligned - sales has quarterly targets and a strong incentive to promise things; product has roadmaps and a strong incentive to protect the team from over-committing. That tension is healthy when managed well. It becomes destructive when one side wins completely.

The failure mode to avoid: the PM who becomes a sales support function - in every deal call, fielding every feature request, letting the pipeline drive the roadmap. A PM who is in every sales call is not doing their actual job. Good PMs develop enough of a selling instinct to be genuinely useful in high-stakes conversations, and then protect their time ruthlessly from everything below that threshold.

Over-promising is one of the most corrosive things that can happen to a product team. A feature that gets sold before it exists creates a different kind of debt than technical debt, and it is harder to pay down. Once sales learns that commitments can be extracted by the right customer in the right deal, the dynamic is very difficult to reverse.

### Organizational Influence

PMs almost always have less formal authority than they have responsibility. That is a feature, not a bug - it forces a particular kind of discipline.

When hitting real resistance from a stakeholder, the first instinct should be to understand it rather than overcome it. Resistance usually has a reason. Sometimes it is a legitimate concern that has not been accounted for. Sometimes it is a misunderstanding. Sometimes it is a protection of turf or a different set of priorities. Those require different responses.

PMs who treat alignment as an obstacle course - figure out what each stakeholder wants to hear and tell them that - produce short-term wins and long-term distrust. The approach that works is to understand what someone actually cares about, figure out whether there is a version of the plan that addresses it legitimately, and adjust accordingly. If there is not, be honest about the tradeoff.

There will be times when you have tried to drive alignment and cannot get there. Not everyone will think they should pull in the same direction, and while you should not assume bad intent, you may not be able to break through deeply held beliefs or divergent motivations. When you have genuinely exhausted your options, escalate - come to me (or your manager) to check whether you are missing context you do not have, and to ask for help. Do not wait until the situation is a crisis, and do not treat escalation as a failure. It is how the organization is supposed to work.

### Storytelling and Communication

PMs need to be effective communicators across very different audiences. The same product decision looks completely different to an engineer, an executive, a customer, and a frontline team member. A good PM can tell the right version of the story to each of them.

This is not about spinning the message. It is about calibrating the level of abstraction and emphasizing what each audience actually cares about. An executive wants the strategic rationale and the risk. An engineer wants the problem and space to figure out the solution. A customer wants to know what is in it for them.

As you meet with people, try to assess where they are coming from relative to your product. What are their motivations? Are they a numbers person who needs to see the financial logic? Do they respond to customer stories and human experience? Are they excited by the technology itself? What do you want them to take away from the conversation - both factually and emotionally? Putting yourself in their shoes before you walk in is not a soft skill; it is the difference between a conversation that moves something and one that does not.

As you get to know people better, pay attention to how they tell their own stories and ask their own questions. The way someone frames a problem tells you a lot about how they want to hear solutions. Over time you will develop an intuition for how specific people want information delivered to them. That intuition is worth building deliberately, not waiting for it to arrive on its own.

If you can only tell one version of a story, you will be less effective than someone who can tell three.

Precision in language matters. Vague language in product work produces vague thinking and vague outcomes.

---

## Delivering Value

### Shipping is Not the Same as Launching

These words get used interchangeably and they mean very different things.

Shipping means the code is in production. Launching means the product is actually in the hands of the people it was built for, and those people know what to do with it. A launch requires that sales knows who to sell to and how to talk about it, that prospective buyers understand why to buy it, and that users understand how to use it. All three have to be true. If any one of them is missing, the product ships but does not land.

PMs frequently underinvest in the launch. The hard work of building is done, the energy is gone, and the GTM motion gets treated as someone else's problem. It is not. A product that ships and sits unused is not a success. The PM owns the outcome, not just the delivery.

### Change Management

Getting a customer to buy a product is not the job. Getting them to actually use it is.

A signed contract and a successful deployment are very different outcomes, and the gap between them is where a lot of product value disappears. If users are not adopting the product, the PM needs to care about that as a product problem - not hand it to customer success and move on. Adoption is signal. When it is missing, the question is why: is it a product problem, a training problem, a change management problem inside the customer's organization, or a mismatch between who bought it and who has to use it?

In enterprise software especially, the people who buy the product are almost never the people whose workflows it disrupts. The product needs to earn adoption by making the user's day better, not just by satisfying the buyer's procurement criteria. Behavior change is hard even when the tool is good. The implementation strategy needs to account for that.

The PM's job is not done at launch. It is done when the product is working in the customer's hands.

---

## Running the Business

### Strategy, Portfolio, and Roadmapping

At the portfolio level, investments should make each other more valuable. Products that share infrastructure, customer relationships, data, or go-to-market motion create compounding returns that individual products cannot. When evaluating where to place bets, the question is always: does this strengthen the portfolio, or is it a standalone bet?

Portfolio allocation is about directing investment toward areas that will create the highest return for the business. Those returns take different shapes - new markets, new customer segments, expansion revenue, churn mitigation, reduced operating cost. Not all of them look the same on a quarterly P&L, which means making the case for each requires translating it into terms the business can actually evaluate. That is the PM's job, not finance's.

Roadmapping is the practice of matching portfolio priorities to a realistic sense of when things can actually launch - not just ship. Customer expectations matter as much as technical timelines. A feature that arrives six months after the market expected it may land worse than if it had never been promised.

PMs should not assume their projects will get funded. Part of the job is making the investment case - articulating why this bet, at this time, with this level of resource, creates more value than the alternatives.

### Portfolio and Resource Allocation

One of the most consistently underestimated realities in product work: engineering capacity is much scarcer than it appears on paper. When you account for bug fixes, on-call support, technical debt, infrastructure maintenance, and the baseline cost of keeping existing products running, it is common for a team to have less than 20 percent of its engineering capacity actually available for new feature work. PMs who plan roadmaps without a clear-eyed view of that constraint are setting themselves up to overpromise and underdeliver.

This is also why engineering investments are so hard to make and so valuable when they happen. Every point of capacity freed up through reliability improvements or debt reduction is leverage on everything that comes after it.

Killing products is part of the job. A product that is not worth investing in is probably not worth maintaining at its current cost either. But sunset decisions are politically hard and tend to get deferred until they become crises. The discipline is doing that assessment proactively.

In practice, keep a rough mental model of how capacity is allocated: what percentage is keeping existing commitments, what is paying down debt, what is genuinely available for new bets. That framing changes the conversation from "why can't we build more things" to "what are we actually choosing to do with the capacity we have."

### Metrics and Outcomes

Product work should be tied to actual business outcomes - not just operational metrics. This is harder than it sounds.

Operational metrics matter as early signals. Activation rate, feature engagement, support ticket volume - these tell you something is working or not working, and they move faster than revenue. But they are directional indicators, not the point. A PM who hits their engagement metric while the business outcome moves the wrong way has the wrong mental model of their job.

The discipline to build: what is the business outcome we are trying to affect, what data would tell us we are moving it, and how confident are we that our operational proxies actually point in the right direction? That last question is often skipped and often wrong.

---

## The Craft in the Age of AI

### The Bottleneck Has Moved

Building is no longer the expensive part. AI has dramatically reduced the cost and time required to produce working prototypes, generate options, and iterate on designs. In principle, you could build thousands of prototypes. The constraint is not production - it is knowing what to build and who to test it with.

This means the highest-leverage PM skill has shifted. The question is no longer "can we build this" but "what exactly do we want to learn, what is the minimum we need to build to learn it, and who are the right people to test it with?" The last part - finding the right customers and getting in front of them - is the bottleneck AI cannot fix. Customer access and relationship quality matter more than they did before, not less.

### What This Means for Junior PMs

As more of the time-consuming analytical and synthesis work moves to AI - market research, requirements drafting, summarizing customer feedback, structuring documents - junior PMs have an opportunity that did not exist before. They can spend more time on the higher-order skills that used to require years to develop: customer relationships, developing taste for what problems are worth solving and what hypotheses are worth testing, learning to read a room, practicing the judgment calls.

The risk is that junior PMs use AI to produce more output without developing the underlying thinking. Output is easy to generate. Judgment is not. Use AI to accelerate the work, not to avoid the hard parts.

### PM and Engineering in the AI Era

The boundary between PM and engineering is getting more porous, and that is a good thing. PMs can now hand engineers working prototypes rather than wire frames or written specs. Engineers may sit in more customer meetings and form independent views about the strategy or approach. The overlap will create occasional friction and a lot of value.

The right frame is a team sport. You are on the same side. When an engineer challenges your direction based on something they observed in a customer meeting, that is the relationship working. When you bring them a prototype you built to test an idea, that is also the relationship working. Treat the expanded overlap as an asset.

The PM's job in this environment is not to defend territory - it is to maintain clarity about the goals, the customer, and the criteria for success, while staying genuinely open to how the path gets there.

---

*Last updated: March 2026*
*This is a living document. Feedback welcome.*
