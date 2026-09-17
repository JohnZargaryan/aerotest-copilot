import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

function App() {
  return (
    <main>
      <header><a href="#overview" className="brand">AEROTEST <span>COPILOT</span></a><span className="tag">Development preview</span></header>
      <section id="overview" className="hero">
        <p className="eyebrow">SIMULATION & TEST INVESTIGATION</p>
        <h1>Understand the fault.<br /><em>Follow the evidence.</em></h1>
        <p className="intro">A software engineering workbench for exploring a fictional research-aircraft subsystem, checking requirements, and investigating results.</p>
        <div className="notice"><span className="dot" /> In development · Healthy-baseline runs are available through the CLI; web execution and chat are not available yet.</div>
      </section>
      <section aria-labelledby="foundation-title" className="foundation">
        <div><p className="eyebrow">ENGINEERING FOUNDATION</p><h2 id="foundation-title">A foundation we can test.</h2><p>Start with precise inputs and explicit boundaries. Add behavior only after the contracts agree.</p></div>
        <ol>
          <li><span>01</span><div><h3>Define the inputs</h3><p>Versioned configuration with fixed simulation ticks and bounded durations.</p></div></li>
          <li><span>02</span><div><h3>Verify the boundary</h3><p>C++ and Python share acceptance cases for valid and invalid configurations.</p></div></li>
          <li><span>03</span><div><h3>Build toward evidence</h3><p>The healthy baseline produces repeatable telemetry and state events. Fault scenarios and investigations are planned.</p></div></li>
        </ol>
      </section>
      <footer><strong>Educational civilian simulation</strong><p>Not flight software or a validated physical model. Developed with AI assistance.</p></footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
