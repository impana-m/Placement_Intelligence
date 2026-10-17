// Fetches graph data from /api/graph-data and renders it with vis-network
document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("graph-container");
    if (!container) return;
    if (typeof vis === "undefined") {
        container.innerHTML = '<p class="text-muted">Graph visualization library not loaded.</p>';
        return;
    }

    fetch("/api/graph-data")
        .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
        })
        .then(function (data) {
            var nodes = [];
            var edges = [];

            data.elements.forEach(function (el) {
                if (el.data.source && el.data.target) {
                    edges.push({
                        from: el.data.source,
                        to: el.data.target,
                        label: (el.data.label || "").replaceAll("_", " "),
                        arrows: "to",
                        color: el.data.label === "conflicts_with" ? { color: "#c62828" } : { color: "#5b8def" },
                    });
                } else {
                    nodes.push({
                        id: el.data.id,
                        label: el.data.label,
                        color: el.data.status === "Active" ? "#d4edda" : "#eee",
                    });
                }
            });

            new vis.Network(
                container,
                { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
                {
                    layout: { improvedLayout: true },
                    physics: { stabilization: true },
                    nodes: { shape: "box", font: { size: 13 } },
                }
            );
        })
        .catch(function (err) {
            console.error("Graph fetch failed:", err);
            container.innerHTML = '<p class="text-muted">Unable to load relationship graph.</p>';
        });
});
