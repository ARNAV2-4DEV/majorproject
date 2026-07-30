import { useState } from 'react';
import { api } from '../api/client';
import './Diet.css';

const DEFAULT_FORM = {
  weight_kg: 70,
  height_cm: 175,
  age: 22,
  sex: 'male',
  activity_level: 'moderate',
  goal: 'maintain',
  diet_preference: 'vegetarian',
  budget_level: '',
  cooking_access: '',
};

export default function Diet() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleCalculate(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        weight_kg: Number(form.weight_kg),
        height_cm: Number(form.height_cm),
        age: Number(form.age),
        budget_level: form.budget_level || null,
        cooking_access: form.cooking_access || null,
      };
      const data = await api.calculateDiet(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleChatSubmit(e) {
    e.preventDefault();
    const text = chatInput.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: 'user', text }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const data = await api.dietChat(text, result?.calorie_data ?? null);
      setMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Couldn't reach the coach: ${err.message}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <div className="container diet-page">
      <p className="eyebrow">Nutrition</p>
      <h1 className="diet-page__title">Diet</h1>
      <p className="diet-page__sub">
        Set your actual constraints - budget and cooking access matter as
        much as your goal. Leave them unset for a general plan.
      </p>

      <div className="diet-page__grid">
        <form className="diet-form" onSubmit={handleCalculate}>
          <div className="diet-form__row">
            <label>
              Weight (kg)
              <input
                type="number"
                value={form.weight_kg}
                onChange={(e) => updateField('weight_kg', e.target.value)}
                required
              />
            </label>
            <label>
              Height (cm)
              <input
                type="number"
                value={form.height_cm}
                onChange={(e) => updateField('height_cm', e.target.value)}
                required
              />
            </label>
            <label>
              Age
              <input
                type="number"
                value={form.age}
                onChange={(e) => updateField('age', e.target.value)}
                required
              />
            </label>
          </div>

          <div className="diet-form__row">
            <label>
              Sex
              <select value={form.sex} onChange={(e) => updateField('sex', e.target.value)}>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </label>
            <label>
              Activity level
              <select
                value={form.activity_level}
                onChange={(e) => updateField('activity_level', e.target.value)}
              >
                <option value="sedentary">Sedentary</option>
                <option value="light">Light</option>
                <option value="moderate">Moderate</option>
                <option value="active">Active</option>
                <option value="very_active">Very active</option>
              </select>
            </label>
            <label>
              Goal
              <select value={form.goal} onChange={(e) => updateField('goal', e.target.value)}>
                <option value="lose">Lose weight</option>
                <option value="maintain">Maintain</option>
                <option value="gain">Gain weight</option>
              </select>
            </label>
          </div>

          <div className="diet-form__row">
            <label>
              Diet preference
              <select
                value={form.diet_preference}
                onChange={(e) => updateField('diet_preference', e.target.value)}
              >
                <option value="vegetarian">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="non_vegetarian">Non-vegetarian</option>
              </select>
            </label>
            <label>
              Budget
              <select
                value={form.budget_level}
                onChange={(e) => updateField('budget_level', e.target.value)}
              >
                <option value="">No constraint</option>
                <option value="low">Low (hostel / tight budget)</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
            <label>
              Cooking access
              <select
                value={form.cooking_access}
                onChange={(e) => updateField('cooking_access', e.target.value)}
              >
                <option value="">No constraint</option>
                <option value="none">None (mess / canteen only)</option>
                <option value="limited">Limited (kettle / microwave)</option>
                <option value="full">Full kitchen</option>
              </select>
            </label>
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Calculating…' : 'Build my plan'}
          </button>
          {error && <p className="error-text">{error}</p>}
        </form>

        <div className="diet-result">
          {!result && <p className="diet-result__empty">Your plan will appear here.</p>}

          {result && (
            <>
              <div className="stat-row">
                <div className="stat">
                  <span className="stat__value">{result.calorie_data.bmi}</span>
                  <span className="stat__label">BMI ({result.calorie_data.bmi_category})</span>
                </div>
                <div className="stat">
                  <span className="stat__value">{result.calorie_data.target_calories}</span>
                  <span className="stat__label">kcal / day target</span>
                </div>
              </div>

              <h3 className="diet-result__heading">Meal plan</h3>
              <ul className="meal-list">
                {Object.entries(result.meal_plan.meals).map(([slot, meal]) => (
                  <li key={slot} className="meal-list__item">
                    <span className="meal-list__slot">{slot}</span>
                    <span className="meal-list__name">{meal.name}</span>
                    <span className="meal-list__cal">{meal.calories} kcal</span>
                  </li>
                ))}
              </ul>

              {result.grocery_list.length > 0 ? (
                <>
                  <h3 className="diet-result__heading">Grocery list</h3>
                  <p className="grocery-list">{result.grocery_list.join(', ')}</p>
                </>
              ) : (
                <p className="grocery-list grocery-list--empty">
                  Nothing to buy - every meal is mess-hall / canteen food.
                </p>
              )}
            </>
          )}
        </div>
      </div>

      <div className="chat-panel">
        <h3 className="diet-result__heading">Ask the coach</h3>
        <div className="chat-panel__messages">
          {messages.length === 0 && (
            <p className="chat-panel__empty">
              Ask anything - "I don't eat dairy, what should I have for breakfast?"
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={m.role === 'user' ? 'chat-bubble chat-bubble--user' : 'chat-bubble'}
            >
              {m.text}
            </div>
          ))}
          {chatLoading && <div className="chat-bubble">Thinking…</div>}
        </div>
        <form className="chat-panel__input-row" onSubmit={handleChatSubmit}>
          <input
            type="text"
            placeholder="Ask a question…"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={chatLoading}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}