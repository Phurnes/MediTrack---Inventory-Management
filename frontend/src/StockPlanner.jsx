
import { useCallback, useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/planner/";

export default function StockPlanner() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPlan = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error(
          `Planner request failed (${response.status}).`
        );
      }

      setPlan(await response.json());
    } catch (err) {
      setError(err.message || "Could not load the stock plan.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlan();

    const onUpdate = () => loadPlan();

    window.addEventListener(
      "meditrack:inventory-updated",
      onUpdate
    );

    return () => {
      window.removeEventListener(
        "meditrack:inventory-updated",
        onUpdate
      );
    };
  }, [loadPlan]);

  if (loading && !plan) {
    return (
      <section className="planner-panel">
        <h2>Smart Stock Planner</h2>
        <p>Loading inventory recommendations...</p>
      </section>
    );
  }

  if (error && !plan) {
    return (
      <section className="planner-panel">
        <h2>Smart Stock Planner</h2>
        <p className="planner-error">{error}</p>
        <button onClick={loadPlan}>Retry</button>
      </section>
    );
  }

  if (!plan) return null;

  return (
    <section className="planner-panel" id="planner">
      <div className="planner-heading">
        <div>
          <h2>Smart Stock Planner</h2>
          <p>Replenishment recommendations from your inventory</p>
        </div>

        <button onClick={loadPlan} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <p className="planner-error">{error}</p>}

      <div className="planner-stats">
        <article className="planner-stat">
          <span>Medicine groups</span>
          <strong>{plan.total_medicines}</strong>
        </article>

        <article className="planner-stat">
          <span>Need restocking</span>
          <strong>{plan.medicines_to_reorder}</strong>
        </article>

        <article className="planner-stat">
          <span>Suggested units</span>
          <strong>{plan.total_suggested_units}</strong>
        </article>
      </div>

      <div className="planner-table-wrapper">
        <table className="planner-table">
          <thead>
            <tr>
              <th>Medicine</th>
              <th>Usable stock</th>
              <th>Target stock</th>
              <th>Expired stock</th>
              <th>Expiring soon</th>
              <th>Suggested order</th>
              <th>Priority</th>
            </tr>
          </thead>

          <tbody>
            {plan.items.map((item) => (
              <tr key={`${item.name}-${item.category}`}>
                <td>
                  <strong>{item.name}</strong>
                  <small>{item.category}</small>
                </td>

                <td>{item.usable_stock}</td>
                <td>{item.target_stock}</td>
                <td>{item.expired_stock}</td>

                <td>
                  {item.expiring_soon_stock}
                  <small>
                    {item.expiring_soon_batches} batch(es)
                  </small>
                </td>

                <td>
                  <strong>{item.suggested_order}</strong>
                </td>

                <td>
                  <span
                    className={`planner-priority priority-${item.priority
                      .toLowerCase()
                      .replaceAll(" ", "-")}`}
                  >
                    {item.priority}
                  </span>
                </td>
              </tr>
            ))}

            {plan.items.length === 0 && (
              <tr>
                <td colSpan="7">No medicines found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="planner-note">
        Expired batches are excluded from usable stock. Review expiry
        risks before placing an order.
      </p>
    </section>
  );
}
