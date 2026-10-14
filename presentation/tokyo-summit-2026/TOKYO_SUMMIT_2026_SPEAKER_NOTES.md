# Tokyo Summit 2026 — Speaker Notes

**Presentation:** Revisiting the Promise of Automated MEP Quantity Takeoff  
**Event:** buildingSMART International Summit Tokyo 2026  
**Date:** October 7, 2026  
**Working Group:** ENMA-WG

> These notes correspond to the presentation delivered at the buildingSMART International Summit Tokyo 2026. They are provided as supplementary material to the presentation slides. The substantive wording below is preserved from the supplied presentation notes.

## Slide 1 — Title

**Original note metadata:** Tujiya　約1分

Good afternoon, everyone.
My name is Nobuhiro Tujiya from TONETS Corporation, and I lead the ENMA Working Group in Japan.
This Tokyo Summit is our first opportunity to share the work of ENMA-WG with the international buildingSMART community.
ENMA stands for Engineering Meaning Automation. Although the name may sound a little Japanese, our goal is to develop engineering knowledge that can be shared internationally through openBIM.
Today, we will revisit a very old promise of BIM: automated MEP quantity takeoff.
Our main presenter is Nyan Kyaw Kaung from SANKEN SETSUBI KOGYO.
Nyan, please begin.


## Slide 2 — ENMA-WG　約45秒

**Original note metadata:** Nyan

Thank you, Tujiya-san.
First, let me briefly introduce ENMA-WG.
ENMA is an industry-led working group in Japan. We have continued practical openBIM research through more than one hundred working meetings.
We experiment with tools such as JIZO, Bonsai, IFC.js, IfcTester, and AI-based technologies.
Our purpose is not simply to exchange BIM data.
We want to understand how openBIM data can become practical engineering knowledge.


## Slide 3 — Mission　約50秒

Building services engineering contains a great deal of practical knowledge.
Engineers accumulate this knowledge through design, construction, operation, and many years of experience.
But much of this knowledge remains tacit. It exists in people and organizations, rather than in digital information.

BIM data alone cannot express all of it.
ENMA's mission is to transform this tacit knowledge into open engineering knowledge, using IFC, IDS, bSDD and AI, and connect it with international openBIM standards.
Our goal is simple: Engineering Knowledge for Everyone.


## Slide 4 — Philosophy　約30秒

This leads to a simple philosophy.
Geometry alone is not enough.
Properties alone are not enough.
And AI alone is not enough.
Engineering knowledge is the missing layer that gives BIM information practical engineering meaning.


## Slide 5 — Revisiting the Promise　約1分30秒

Now, let us return to the promise in the title of this presentation.
For many years, BIM has promised that digital models would make quantity takeoff automatic.
And in one sense, this is true.
From geometry, we can measure something like pipe length.
But estimation requires more than measurement.
Required properties may be incomplete, and engineering context affects what should actually be estimated.
For example, pipe length alone may not determine the insulation requirement. We may also need the construction location and engineering rules.
So our question is:
What is required to turn IFC data into estimable MEP quantities?
This is the key distinction in our research:
Measurement is not the same as estimation.


## Slide 6 — ENMA Approach　約1分30秒

Our approach starts with IFC data.
IFC provides elements, properties, quantities, ports, and other information.
IDS helps us check whether required information is present.
bSDD can provide shared semantic meaning.
Engineering knowledge and rules then add the context needed for estimation.
AI can assist when information is incomplete or ambiguous.
But AI does not replace engineering judgment.
The objective is to move from IFC data, through engineering meaning, to a quantity that is suitable for engineering use.
The insulation example shown here illustrates this approach. It is a future application and is not yet implemented in our current PoC.


## Slide 7 — Real IFC PoC Results　約1分45秒

We did not want to discuss this only as a concept.
So we tested the approach using a real Japanese Ministry of Land, Infrastructure, Transport and Tourism BIM model.
For the current PoC, pipe quantity extraction is implemented. Ducts are in progress, and equipment is future work.
Using IfcOpenShell, we identified 252 pipe segments and 81 pipe fittings.
The current centerline-based total pipe length is 649.090 meters.
We also classified the pipe length by direction: approximately 376 meters horizontal and 273 meters vertical.
We extracted information such as storey, system, diameter, direction, height, fittings and ports.
These are not conceptual numbers.
They were extracted from an actual IFC model.


## Slide 8 — What Does “Length” Mean?　約1分45秒

But when we obtained 649.090 meters, another question appeared.
What exactly does “length” mean?
IFC may contain a property length.
We can calculate a geometry length.
We can measure a centerline length.
We may need a net pipe length after considering fittings.
And finally, the quantity used for estimation may be different again.
In our current PoC, the reported value is centerline-based, and fitting length has not yet been deducted.
So the measurable quantity is not always the estimable quantity.
This is where engineering meaning, human review and engineering rules become important.


## Slide 9 — ENMA Quantity Takeoff Data Model　約2分

To make this process traceable, we are developing this data model.
At the center is a simple flow.
IFC Elements become Inference Results.
When necessary, engineers review those inferences.
Engineering rules are then evaluated, producing element-level quantity results and quantity summaries.
Around this flow, we connect several types of information.
IFC provides element properties, ports and connections.
Specifications and IDS provide project requirements.
Engineering masters provide shared concepts such as fluids, work locations, pipe materials, sizes, insulation and painting types.
Engineering rules determine how this information affects quantities.
And calculation evidence records how each result was produced.
The important point is traceability.
We do not want only a number.
We want to know which IFC data, engineering meaning, human decision and rule produced that number.


## Slide 10 — Beyond Quantity Takeoff　約1分15秒

And quantity takeoff is not the end of this story.
Once quantity is connected with classification, materials, properties and cost information, the same engineering information can support other workflows.
It can support cost estimation, construction progress measurement, procurement and equipment selection.
For example, pipe length combined with diameter, material, standard and cost information can eventually support estimation and procurement.
These downstream applications are not implemented in the current PoC.
The important idea is that quantity takeoff becomes a starting point for reusable engineering information.


## Slide 11 — ENMA 3.0 Vision　約1分30秒

This brings us to our broader ENMA 3.0 vision.
We are not trying to replace existing BIM or engineering software.
Existing tools and workflows remain in place.
ENMA proposes an open engineering knowledge layer around them.
IFC provides interoperable data.
IDS validates information requirements.
bSDD provides shared semantics.
Engineering knowledge provides reusable rules and intent.
Knowledge graphs can connect those concepts, and AI-assisted reasoning can help interpret them.
Quantity takeoff is the application we are demonstrating today.
In the future, the same knowledge foundation may support equipment selection, code compliance, carbon and LCA assessment, lifecycle cost and facility knowledge.
In short:
openBIM connects data. Engineering Knowledge connects decisions.


Thank you, Nyan.
Let me close with three words:
Measure. Understand. Reuse.
IFC allows us to measure engineering information.
Engineering knowledge helps us understand what that information means.
And open standards allow that information to be reused.
We started this presentation by revisiting the promise of automated MEP quantity takeoff.
Our conclusion is that quantity takeoff is not the final goal.
It is one application of openBIM data.
The greater opportunity is to transform BIM data into reusable engineering knowledge that can continue into estimation, construction, procurement, facility management and sustainability.
ENMA is still at an early stage.
But we believe this PoC is one practical step from BIM data toward open engineering knowledge.


## Slide 13 — Thank You

**Original note metadata:** GitHub QR / Tujiya　約40秒

Thank you very much for your attention.
ENMA is an open and collaborative research activity.
Our Quantity Takeoff PoC is available on GitHub through this QR code.
We welcome your comments, ideas and feedback.
We hope to continue connecting practical MEP engineering knowledge with the international openBIM community.
Engineering Knowledge for Everyone.
Let’s build Open Engineering together.
Thank you.
