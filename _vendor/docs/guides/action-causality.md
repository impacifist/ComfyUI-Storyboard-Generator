# Action prerequisites and causal continuity

Shared application policy for storyboard generation, regeneration, semantic review and video conversion. Apply it to every consequential action or change, regardless of setting or genre. Examples illustrate the reasoning; they are not a list of special-case fixes. Follow the user's fictional world rules and output-language requirements.

## Plan backward, then play forward

Before finalizing the shots, reason backward from the requested outcome: what must already be true for each action to succeed? Then mentally play the sequence forward from the supplied initial situation. For each consequential action, check:

1. **Actor and target:** who acts, on whom or what, and with what intended result?
2. **Required conditions:** what location, access, posture, object state, possession, ability, information or preceding event makes the action possible?
3. **Evidence:** which input fact, established starting condition, earlier action or explicit time transition supplies each required condition? Do not treat a future event as evidence for an earlier action.
4. **Order and time:** are preparation, contact, action and response in a possible order, with enough time? Which steps genuinely overlap and which depend on completion of another step?
5. **Result and persistence:** what changes, what remains true, and what does the next action inherit? A condition persists until an actual event changes it. Track resources consumed, objects moved or handed over, and information learned.

This is internal planning, not a request for hidden reasoning in the output. Record the observable result in the existing storyboard fields. Do not add schema fields or a separate prerequisite checklist to the JSON response.

## Check more than physical movement

- **Space and access:** reachable destinations, traversable paths, available openings, distance and travel time. A cut does not teleport a character or remove an obstacle.
- **Objects and resources:** existence, location, possession, availability and usable state. An object must be obtained before use, and a handoff changes who holds it. Do not restore a consumed or broken resource without an established cause.
- **Body and environment:** starting posture, occupied hands, support, motion, mechanisms and environmental changes. Do not describe incompatible states simultaneously.
- **Perception and knowledge:** a response needs a stimulus the character can actually hear, see, receive or already know. A private thought is not automatically shared information. Concealed information remains concealed until an established disclosure or observation.
- **Intention and emotional response:** a decision or meaningful change of attitude needs support from the persona, existing context or a preceding stimulus. Not every feeling needs a spoken explanation or a new backstory; preserve ambiguity when intended. Do not force a reconciliation simply because one character speaks.
- **Time and consequence:** preparation precedes execution when required, information arrives before it is acted upon, and reactions follow their stimulus. Preserve established injuries, fatigue, changed relationships and other relevant effects until the story changes them.

For example, a character answers a phone only after an established incoming call and access to the device; reacts to a message after receiving/reading it; drinks from an available vessel; enters through an accessible doorway; or leaves an ordinary vehicle after it stops and the exit becomes usable. Use the same reasoning for cooking, an argument, a chase, an encounter or any other situation. Do not copy these examples into unrelated stories.

## Repair gaps economically during generation

If a necessary condition is already established, reuse it; do not repeat its setup. If the scene begins after preparation, establish the relevant starting state without replaying the entire preparation. The audience need not see every mundane step, but the action must be possible and any omitted transition must be understandable.

When the brief supplies only an outcome, infer only the minimal ordinary setup consistent with the user's intent. Distinguish inferred setup in assumptions and embody it in visual/actions/continuity; assumptions alone cannot repair contradictory on-screen action. Use existing start_state/end_state for character and prop changes. Describe other necessary environment or information states in the existing visual/actions/continuity fields.

Integrate preparation and consequences into the requested shot count and duration. They may occur within a continuous shot or an understandable transition; they do not each require a new shot. Allocate time rather than compressing dependent steps into one instant. Do not invent an unrelated event, additional character, crucial resource, secret knowledge or personality change merely to make an action work. If a conflict cannot be resolved within the user's constraints, disclose it in assumptions and advisory review rather than pretending it has been resolved or silently changing the requested outcome.

In regeneration, preserve locked shots exactly. Work with the editable surrounding shots where possible; identify unresolved conflicts in review. Explicit stunts, surreal action and fictional capabilities override ordinary-world defaults, but their own established rules and consequences still apply.

## Review and conversion have different authority

Semantic review checks the whole sequence for missing enabling conditions, reversed dependencies, unearned knowledge, unexplained changes and forgotten consequences. Distinguish an explicit contradiction from missing information, and both from an intentional ellipsis supported by context. Cite the affected shot and relevant preceding context, then suggest the smallest repair. Do not require visible setup for facts already established or invent problems from optional details. Report concerns as advisory findings, not new automatic save failures.

Video conversion preserves the approved causal design. Translate its enabling conditions, action order and consequences into English and carry still-relevant states into later clip contexts. A technical clip boundary does not reset possession, access, motion, knowledge or relationships. Only describe a state change when the approved source supplies its cause; do not replay completed setup at each clip opening. Do not anticipate a later action inside the earlier segment.

If the approved storyboard is missing a prerequisite or contains a contradiction, put a specific revision suggestion in advisory notes. Do not silently invent preparation, retime speech, alter a locked/source shot or change the outcome during conversion. Exact original dialogue and the approved plan remain authoritative. These instructions guide AI reasoning; structural validation alone cannot guarantee real-world plausibility or generated-video quality.
