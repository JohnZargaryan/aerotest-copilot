import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RecordedRunPanel } from "./RecordedRunPanel";
import "./style.css";

createRoot(document.getElementById("root")!).render(<StrictMode><main className="recorded-demo">
  <header><a href="#overview" className="brand">AEROTEST <span>COPILOT</span></a><span className="tag">Interactive recorded demo</span></header>
  <section id="overview" className="hero">
    <p className="eyebrow">SIMULATION & TEST INVESTIGATION</p>
    <h1>Understand the fault.<br /><em>Follow the evidence.</em></h1>
    <p className="intro">Explore four recorded scenarios from a fictional research-aircraft subsystem. Inspect telemetry, scoped checks and the original records behind each finding.</p>
    <div className="notice"><span className="dot" />Recorded evidence · No backend required · Scripted explanations</div>
    <p><a href="https://johnzargaryan.com/projects/aerotest">← Portfolio case study</a></p>
  </section>
  <RecordedRunPanel />
  <footer><strong>Educational civilian simulation</strong><p>Not flight software or a validated physical model. This browser demo reads saved runs. To generate new runs, use the <a href="https://github.com/JohnZargaryan/aerotest-copilot#start-on-windows" target="_blank" rel="noreferrer">local application</a>.</p></footer>
</main></StrictMode>);
