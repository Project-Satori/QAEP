(() => {
  const PAGE_SIZE = 50;
  const state = { all: [], filtered: [], page: 1 };
  const $ = (id) => document.getElementById(id);
  const els = {
    search: $("search"), year: $("year"), chipset: $("chipset"),
    results: $("results"), count: $("result-count"), page: $("page-label"),
    prev: $("prev"), next: $("next")
  };

  const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[c]);

  async function load() {
    const response = await fetch("./data/index.json");
    if (!response.ok) throw new Error(`Cannot load data index (${response.status})`);
    const index = await response.json();
    const shards = await Promise.all(index.years.map(async item => {
      const res = await fetch(`./data/${encodeURIComponent(item.file)}`);
      if (!res.ok) throw new Error(`Cannot load ${item.file} (${res.status})`);
      return res.json();
    }));
    state.all = shards.flat();
    $("total-count").textContent = Number(index.record_count).toLocaleString();
    $("year-count").textContent = index.years.length.toLocaleString();
    $("chipset-count").textContent = new Set(state.all.map(r => r.chipset).filter(Boolean)).size.toLocaleString();

    for (const item of index.years) {
      const option = document.createElement("option");
      option.value = item.year; option.textContent = `${item.year} (${item.count})`;
      els.year.append(option);
    }
    const chipsets = [...new Set(state.all.map(r => r.chipset).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
    for (const chipset of chipsets) {
      const option = document.createElement("option");
      option.value = chipset; option.textContent = chipset;
      els.chipset.append(option);
    }
    filter();
  }

  function filter() {
    const q = els.search.value.trim().toLowerCase();
    const year = els.year.value;
    const chipset = els.chipset.value;
    state.filtered = state.all.filter(r => {
      if (year && !(r.date_iso || "").startsWith(year)) return false;
      if (chipset && r.chipset !== chipset) return false;
      if (!q) return true;
      return [r.date,r.tag,r.chipset,r.manifest,r.android_version]
        .some(v => String(v ?? "").toLowerCase().includes(q));
    });
    state.page = 1;
    render();
  }

  function render() {
    const total = state.filtered.length;
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * PAGE_SIZE;
    const rows = state.filtered.slice(start, start + PAGE_SIZE);
    els.count.textContent = `${total.toLocaleString()} matching records`;
    els.page.textContent = `Page ${state.page} of ${pages}`;
    els.prev.disabled = state.page <= 1;
    els.next.disabled = state.page >= pages;
    if (!rows.length) {
      els.results.innerHTML = '<tr><td colspan="5" class="empty">No matching releases.</td></tr>';
      return;
    }
    els.results.innerHTML = rows.map(r => `<tr>
      <td>${escapeHTML(r.date)}</td>
      <td>${escapeHTML(r.tag)}</td>
      <td>${escapeHTML(r.chipset)}</td>
      <td>${escapeHTML(r.manifest)}</td>
      <td>${escapeHTML(r.android_version)}</td>
    </tr>`).join("");
  }

  els.search.addEventListener("input", filter);
  els.year.addEventListener("change", filter);
  els.chipset.addEventListener("change", filter);
  $("reset").addEventListener("click", () => {
    els.search.value = ""; els.year.value = ""; els.chipset.value = ""; filter();
  });
  els.prev.addEventListener("click", () => { if (state.page > 1) { state.page--; render(); } });
  els.next.addEventListener("click", () => {
    if (state.page * PAGE_SIZE < state.filtered.length) { state.page++; render(); }
  });

  load().catch(error => {
    console.error(error);
    els.count.textContent = "Failed to load archive";
    els.results.innerHTML = `<tr><td colspan="5" class="empty">${escapeHTML(error.message)}. Check that the JSON data has been imported and committed.</td></tr>`;
  });
})();
