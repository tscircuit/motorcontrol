const workspaces = [
  ["motor-bench.html", "Motor bench"],
  ["single-motor.html", "Single stepper jog"],
  ["gantry.html", "Two-axis gantry"],
  ["three-axis-gantry.html", "Three-axis gantry"],
  ["bldc.html", "Brushless motor (BLDC)"],
];

const resources = [
  ["manual/NEMA17-Kit-Booklet.pdf", "NEMA17 kit booklet (PDF)"],
  ["firmware.html", "Firmware & desktop app"],
  ["assets.html", "Printable parts"],
];

function NavGroup({ title, links, page }: { title: string; links: string[][]; page: string }) {
  return (
    <details className="navGroup" name="motorcontrol-navigation">
      <summary>{title}</summary>
      <div className="navList">
        {links.map(([href, label]) => (
          <a key={href} href={href} aria-current={page === href ? "page" : undefined}>{label}</a>
        ))}
      </div>
    </details>
  );
}

export function SiteHeader({ page }: { page: string }) {
  return (
    <header className="siteHeader">
      <nav className="siteNav" aria-label="Motorcontrol">
        <a className="brand" href="/">
          <img src="assets/tscircuit-mark.png" width="30" height="30" alt="tscircuit" />
          Motorcontrol
        </a>
        <div className="navItems">
          <a href="/" aria-current={page === "index.html" ? "page" : undefined}>Get started</a>
          <NavGroup title="Workspaces" links={workspaces} page={page} />
          <NavGroup title="Resources" links={resources} page={page} />
        </div>
      </nav>
    </header>
  );
}
