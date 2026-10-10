
import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/medicines/";

const emptyForm = {
  name: "",
  category: "TABLET",
  batch_number: "",
  manufacturer: "",
  quantity: "0",
  expiry_date: "",
};

const categories = [
  ["TABLET", "Tablet"],
  ["CAPSULE", "Capsule"],
  ["SYRUP", "Syrup"],
  ["INJECTION", "Injection"],
  ["OINTMENT", "Ointment"],
  ["DROPS", "Drops"],
  ["OTHER", "Other"],
];

function displayDate(value) {
  if (!value) return "—";
  const [year, month, day] = value.split("-");
  return `${day}-${month}-${year}`;
}


function getStatus(medicine) {
  if (medicine.status) return medicine.status;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const expiry = new Date(`${medicine.expiry_date}T00:00:00`);
  const daysLeft = Math.round((expiry - today) / 86400000);

  if (daysLeft < 0) return "Expired";

  const warnings = [];

  if (daysLeft <= 30) warnings.push("Expiring Soon");
  if (medicine.quantity < 20) warnings.push("Low Stock");

  return warnings.length ? warnings.join(", ") : "In Stock";
}


function App() {
  const [medicines, setMedicines] = useState([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const request = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });

    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try {
        const data = await response.json();
        detail = Object.entries(data)
          .map(([key, value]) => {
            const text = Array.isArray(value) ? value.join(", ") : value;
            return `${key}: ${text}`;
          })
          .join(" | ");
      } catch {
        // Keep the HTTP status message if the response isn't JSON.
      }
      throw new Error(detail);
    }

    if (response.status === 204) return null;
    return response.json();
  };

  const loadMedicines = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      // Follow every DRF pagination page so dashboard counts are accurate.
      let url = API_URL;
      const all = [];

      while (url) {
        const data = await request(url);
        if (Array.isArray(data)) {
          all.push(...data);
          url = null;
        } else {
          all.push(...(data.results ?? []));
          url = data.next;
        }
      }

      setMedicines(all);
    } catch (err) {
      setError(
        `Could not load medicines. Ensure Django is running. ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMedicines();
  }, [loadMedicines]);

  const filteredMedicines = useMemo(() => {
    const term = search.trim().toLowerCase();

    return medicines.filter((medicine) => {
      const matchesSearch = [
        medicine.name,
        medicine.batch_number,
        medicine.manufacturer,
      ].some((value) => (value || "").toLowerCase().includes(term));

      const matchesFilter =
        filter === "All" || getStatus(medicine).split(", ").includes(filter);

      return matchesSearch && matchesFilter;
    });
  }, [medicines, search, filter]);

  
  const expiringCount = medicines.filter((medicine) => {
    const status = getStatus(medicine);
    return status.includes("Expiring Soon") || status === "Expired";
  }).length;

  const lowStockCount = medicines.filter((medicine) => {
    return getStatus(medicine).includes("Low Stock");
  }).length;


  const totalUnits = medicines.reduce(
    (total, medicine) => total + Number(medicine.quantity || 0),
    0
  );

  function openAddForm() {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setMessage("");
    setFormOpen(true);
  }

  function openEditForm(medicine) {
    setEditingId(medicine.id);
    setForm({
      name: medicine.name,
      category: medicine.category,
      batch_number: medicine.batch_number,
      manufacturer: medicine.manufacturer || "",
      quantity: String(medicine.quantity),
      expiry_date: medicine.expiry_date,
    });
    setError("");
    setMessage("");
    setFormOpen(true);
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submitMedicine(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const payload = {
        ...form,
        name: form.name.trim(),
        batch_number: form.batch_number.trim(),
        manufacturer: form.manufacturer.trim(),
        quantity: Number(form.quantity),
      };

      const url = editingId ? `${API_URL}${editingId}/` : API_URL;

      await request(url, {
        method: editingId ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });

      setFormOpen(false);
      setForm(emptyForm);
      setEditingId(null);
      setMessage(editingId ? "Medicine updated successfully." : "Medicine added successfully.");
      await loadMedicines();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteMedicine(medicine) {
    const confirmed = window.confirm(
      `Delete ${medicine.name} (batch ${medicine.batch_number})?`
    );
    if (!confirmed) return;

    setError("");
    setMessage("");

    try {
      await request(`${API_URL}${medicine.id}/`, { method: "DELETE" });
      setMessage("Medicine deleted successfully.");
      await loadMedicines();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✚</div>
          <div>
            <h2>MediTrack</h2>
            <p>Inventory Management</p>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <nav>
          <a className="nav-item active" href="#dashboard">
            <span>▦</span> Dashboard
          </a>
          <a className="nav-item" href="#inventory">
            <span>▤</span> Medicine Inventory
          </a>
          <a className="nav-item" href="#alerts">
            <span>♧</span> Expiry &amp; Stock Alerts
          </a>
        </nav>

        <div className="sidebar-footer">
          <div className="footer-dot" />
          <div>
            <strong>MediTrack</strong>
            <p>Medicine safety, simplified.</p>
          </div>
        </div>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div>
            <p className="eyebrow">INVENTORY MANAGEMENT</p>
            <h1>Dashboard</h1>
            <p className="subtitle">
              Monitor your medicine stock and expiry dates.
            </p>
          </div>
          <div className="today-badge">
            <span>◷</span>{" "}
            {new Date().toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
          </div>
        </header>

        {error && (
          <div className="app-message error-message" role="alert">
            <span>{error}</span>
            <button onClick={() => setError("")} aria-label="Dismiss error">×</button>
          </div>
        )}
        {message && (
          <div className="app-message success-message" role="status">
            <span>{message}</span>
            <button onClick={() => setMessage("")} aria-label="Dismiss message">×</button>
          </div>
        )}

        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-icon purple">▤</div>
            <p>Total Medicines</p>
            <h2>{loading ? "—" : medicines.length}</h2>
            <span className="stat-note">Unique inventory records</span>
          </article>
          <article className="stat-card">
            <div className="stat-icon blue">▦</div>
            <p>Total Units in Stock</p>
            <h2>{loading ? "—" : totalUnits}</h2>
            <span className="stat-note">Units across all batches</span>
          </article>
          <article className="stat-card">
            <div className="stat-icon orange">◷</div>
            <p>Expiry Alerts</p>
            <h2>{loading ? "—" : expiringCount}</h2>
            <span className="stat-note">Expired or expiring within 30 days</span>
          </article>
          <article className="stat-card">
            <div className="stat-icon red">!</div>
            <p>Low Stock</p>
            <h2>{loading ? "—" : lowStockCount}</h2>
            <span className="stat-note">Fewer than 20 units</span>
          </article>
        </section>

        <section className="inventory-panel" id="inventory">
          <div className="panel-heading">
            <div>
              <h2>Medicine Inventory</h2>
              <p>Review stock levels and medicine expiry dates.</p>
            </div>
            <div className="panel-actions">
              <span className="record-count">
                {filteredMedicines.length} records
              </span>
              <button className="primary-button" onClick={openAddForm}>
                + Add Medicine
              </button>
            </div>
          </div>

          <div className="toolbar">
            <div className="search-box">
              <span>⌕</span>
              <input
                type="search"
                placeholder="Search medicine, batch or manufacturer..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <select
              aria-label="Filter by status"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="All">All statuses</option>
              <option value="In Stock">In Stock</option>
              <option value="Low Stock">Low Stock</option>
              <option value="Expiring Soon">Expiring Soon</option>
              <option value="Expired">Expired</option>
            </select>
            <button className="secondary-button" onClick={loadMedicines} disabled={loading}>
              Refresh
            </button>
          </div>

          {formOpen && (
            <form className="medicine-form" onSubmit={submitMedicine}>
              <div className="form-heading">
                <h3>{editingId ? "Edit medicine" : "Add medicine"}</h3>
                <button
                  type="button"
                  className="close-button"
                  onClick={() => setFormOpen(false)}
                  aria-label="Close form"
                >
                  ×
                </button>
              </div>

              <div className="form-grid">
                <label>
                  Medicine name *
                  <input name="name" value={form.name} onChange={updateField} required maxLength={150} />
                </label>
                <label>
                  Category *
                  <select name="category" value={form.category} onChange={updateField} required>
                    {categories.map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Batch number *
                  <input name="batch_number" value={form.batch_number} onChange={updateField} required maxLength={100} />
                </label>
                <label>
                  Manufacturer
                  <input name="manufacturer" value={form.manufacturer} onChange={updateField} maxLength={150} />
                </label>
                <label>
                  Quantity *
                  <input name="quantity" type="number" min="0" step="1" value={form.quantity} onChange={updateField} required />
                </label>
                <label>
                  Expiry date *
                  <input name="expiry_date" type="date" value={form.expiry_date} onChange={updateField} required />
                </label>
              </div>

              <div className="form-actions">
                <button type="button" className="secondary-button" onClick={() => setFormOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Saving..." : editingId ? "Save changes" : "Add medicine"}
                </button>
              </div>
            </form>
          )}

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>MEDICINE</th>
                  <th>BATCH NUMBER</th>
                  <th>QUANTITY</th>
                  <th>EXPIRY DATE</th>
                  <th>STATUS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr><td colSpan="6" className="empty-state">Loading inventory...</td></tr>
                )}
                {!loading && filteredMedicines.map((medicine) => {
                  const status = getStatus(medicine);
                  return (
                    <tr key={medicine.id}>
                      <td>
                        <div className="medicine-name">
                          <div className="medicine-avatar">
                            {(medicine.name || "?").charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <strong>{medicine.name}</strong>
                            <span>
                              {categories.find(([value]) => value === medicine.category)?.[1] || medicine.category}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="batch-number">{medicine.batch_number}</td>
                      <td>
                        <strong>{medicine.quantity}</strong>
                        <span className="unit-label"> units</span>
                      </td>
                      <td>{displayDate(medicine.expiry_date)}</td>
                      <td>
                        <span
                          className={`status ${status
                            .split(", ")
                            .map((item) => `status-${item.toLowerCase().replaceAll(" ", "-")}`)
                            .join(" ")}`}
                        >
                          {status}
                        </span>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button className="text-button" onClick={() => openEditForm(medicine)}>
                            Edit
                          </button>
                          <button className="text-button delete-button" onClick={() => deleteMedicine(medicine)}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {!loading && filteredMedicines.length === 0 && (
                  <tr>
                    <td colSpan="6" className="empty-state">
                      {medicines.length === 0
                        ? "No medicines in the database yet. Select Add Medicine to create one."
                        : "No medicines match your search or filter."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            Showing {filteredMedicines.length} of {medicines.length} medicines
          </div>
        </section>

        <section className="notice-panel" id="alerts">
          <div className="notice-icon">!</div>
          <div>
            <h3>Inventory reminders</h3>
            <p>
              Check expiry alerts regularly and review low-stock medicines
              before placing replenishment orders.
            </p>
          </div>
        </section>

        <footer className="page-footer">
          MediTrack · Medicine Expiry &amp; Inventory Management System
        </footer>
      </main>
    </div>
  );
}

export default App;
