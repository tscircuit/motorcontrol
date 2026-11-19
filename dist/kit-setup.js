// The guide presents the existing bench controls. Its only preset is a finite
// move from the printed NEMA17 manual. Connecting never requests power or motion.
(() => {
  const url = new URL(location.href);
  if (url.searchParams.get("setup") !== "nema17") return;

  const el = id => document.getElementById(id);
  const steps = {
    connect: ["Connect your controller", "With both USB cables unplugged, check the motor connection and secure the unloaded motor. Plug a USB data cable from your computer into DATA. Choose Connect board, then select the controller."],
    power: ["Add motor power", "Connect a compatible USB-C PD supply to PWR. Choose a voltage supported by both your kit and supply, then select Request voltage. For kits that support it, try 9 V. Wait for the power to settle."],
    move: ["Try a quarter turn", "Keep the shaft clear and this tab visible. Select Start movement for 50 full steps at 40 steps per second. The move ends automatically. You can press Stop at any time."],
  };
  let sawMove = false;
  let completed = false;
  const indicators = document.querySelectorAll(".kitSteps li");
  const title = document.title;
  function exitGuide() {
    document.body.classList.remove("kitSetup");
    delete document.body.dataset.kitStep;
    document.title = title;
    url.searchParams.delete("setup");
    history.replaceState(history.state, "", url);
    delete window.kitSetup;
  }

  function showStep(step) {
    if (document.body.dataset.kitStep === step) return;
    document.body.dataset.kitStep = step;
    const [heading, instruction] = step === "done"
      ? ["First move complete", "The controller finished its 50-step command. If you saw the shaft turn, you’re ready to explore the full Motor bench. To pack up, disconnect here and unplug PWR and DATA."]
      : steps[step];
    el("kitTitle").textContent = heading;
    el("kitInstruction").textContent = instruction;
    for (const indicator of indicators) {
      if (indicator.dataset.step === (step === "done" ? "move" : step)) indicator.setAttribute("aria-current", "step");
      else indicator.removeAttribute("aria-current");
    }
  }

  el("mode").value = "steps";
  el("resolution").value = "full";
  el("direction").value = "1";
  el("speed").value = "40";
  el("steps").value = "50";
  el("showBench").addEventListener("click", () => {
    exitGuide();
    el("connect").focus();
  });
  document.body.classList.add("kitSetup");
  document.title = "NEMA17 quick start · Motorcontrol";
  showStep("connect");

  window.kitSetup = {
    update(port, live, board) {
      const caps = board?.capabilities;
      if (live && (board.protocol !== 3 ||
          !["rp2040_drv8825", "rp2040_drv8825_pd"].includes(board.board_id) ||
          !caps?.pd_voltages?.length || caps.resolutions?.full !== 1 ||
          caps.full_steps_per_revolution !== 200 || caps.min_speed_sps > 40 ||
          (caps.max_speed_sps != null && caps.max_speed_sps < 40) || caps.max_steps < 50 || board.homing_required || board.homing_active)) {
        exitGuide();
        el("message").textContent = "This controller uses the full Motor bench. Its available controls are shown here.";
        return;
      }
      if (!live) {
        sawMove = completed = false;
        showStep("connect");
      } else if (!board.motor_power_ready && !board.motor_enabled) {
        sawMove = completed = false;
        showStep("power");
      } else {
        if (board.motor_enabled) {
          sawMove = true;
          completed = false;
        } else if (sawMove) {
          completed = board.stop_reason === "Step move complete" && board.steps_executed === 50;
          sawMove = false;
        }
        showStep(completed ? "done" : "move");
      }
      let health = "";
      if (port && !live) health = "Waiting for live board readings. Check the DATA connection.";
      else if (live && (board.driver_fault_asserted || board.sensor_error || board.alarm_active)) {
        health = "The controller reports a fault or alarm. Stop and check the full Motor bench before continuing.";
        el("start").disabled = true;
      }
      if (el("kitHealth").textContent !== health) el("kitHealth").textContent = health;
    }
  };
})();
