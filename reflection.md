# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My UML design will be made to help a user add owner name for identity, the pet hopefully to note which pet species and their name too, list a task what needed for the pet, and note their daily plan, time to do those tasks each.
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

A bit for what I needed to do was fix a few parts in my pawpal_system.py and class_diagram.mmd. I needed to fix the missing or weak relationships between owner and pet on pawpal_system.py, fix a weak link on CareTask, the list under Pet. For logic bottlenecks, I needed to fix some parts on the lists for owners, pets, tasks, and plans such adding an index strategy. For domain-model gaps needed to included missing core scheduling fields for what's included in the CareTask model. Also needed to add strong validation for task_ids and completion_status.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My schedulers, which I named as DailyPlan, tracks whether each task is complete and calculates the plan’s completion progress. It can also detect time conflicts by comparing tasks’ preferred times and durations. Tasks are added to the plan only if they’re due that day, and the app displays them by preferred time. Priority is shown, but the schedule doesn’t use it to choose or fit tasks. I decided which constraints mattered most via prioritizing whether a task is due today, so only tasks scheduled for that day appear in the plan. I also considered preferred time and duration to order tasks and identify overlapping time slots. Priority is recorded and displayed, but doesn't currently determine which tasks make the schedule.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
