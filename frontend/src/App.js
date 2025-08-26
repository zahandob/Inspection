import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import axios from "axios";
import { BrowserRouter } from "react-router-dom";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { toast } from "./hooks/use-toast";
import { ArrowUp, ArrowDown, ThumbsUp, ThumbsDown, Wand2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function useApi() {
  const api = useMemo(() => axios.create({ baseURL: API }), []);
  return api;
}

const SignUp = ({ onCreated }) => {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState({ income_brackets: [], education_levels: [], ethnicity_options: [] });

  const [form, setForm] = useState({
    first_name: "",
    other_given_names: "",
    last_name: "",
    email: "",
    phone_number: "",
    education: "",
    where_you_live: "",
    age: "",
    income_bracket: "",
    interests_text: "",
    ethnicity: "",
  });

  useEffect(() => {
    const loadOpts = async () => {
      try {
        const r = await api.get("/placer/options");
        setOptions(r.data);
      } catch (e) {
        console.error(e);
      }
    };
    loadOpts();
  }, [api]);

  const handle = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const interests = form.interests_text
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .slice(0, 3);
      const payload = {
        first_name: form.first_name,
        other_given_names: form.other_given_names || undefined,
        last_name: form.last_name,
        email: form.email,
        phone_number: form.phone_number || undefined,
        education: form.education || undefined,
        where_you_live: form.where_you_live || undefined,
        age: form.age ? Number(form.age) : undefined,
        income_bracket: form.income_bracket || undefined,
        interests,
        ethnicity: form.ethnicity || undefined,
      };
      const r = await api.post("/placer/signup", payload);
      toast({ title: "Profile created", description: `Welcome ${r.data.first_name}!` });
      onCreated(r.data);
    } catch (e) {
      console.error(e);
      toast({ title: "Error", description: e?.response?.data?.detail || "Failed to create profile" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="glass p-6">
      <CardHeader>
        <CardTitle>Create your profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>First Name</Label>
            <Input name="first_name" value={form.first_name} onChange={handle} required />
          </div>
          <div>
            <Label>Other Given Names</Label>
            <Input name="other_given_names" value={form.other_given_names} onChange={handle} />
          </div>
          <div>
            <Label>Last Name</Label>
            <Input name="last_name" value={form.last_name} onChange={handle} required />
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" name="email" value={form.email} onChange={handle} required />
          </div>
          <div>
            <Label>Phone Number</Label>
            <Input name="phone_number" value={form.phone_number} onChange={handle} />
          </div>
          <div>
            <Label>Education</Label>
            <Select onValueChange={(v) => setForm((f) => ({ ...f, education: v }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select education" />
              </SelectTrigger>
              <SelectContent>
                {options.education_levels.map((o) => (
                  <SelectItem key={o} value={o}>{o}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Where you live</Label>
            <Input name="where_you_live" value={form.where_you_live} onChange={handle} />
          </div>
          <div>
            <Label>Age</Label>
            <Input type="number" min="10" max="100" name="age" value={form.age} onChange={handle} />
          </div>
          <div>
            <Label>Income/Parental Income</Label>
            <Select onValueChange={(v) => setForm((f) => ({ ...f, income_bracket: v }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select bracket" />
              </SelectTrigger>
              <SelectContent>
                {options.income_brackets.map((o) => (
                  <SelectItem key={o} value={o}>{o}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Label>Interests (list 3, comma separated)</Label>
            <Input name="interests_text" value={form.interests_text} onChange={handle} placeholder="e.g. startups, tennis, photography" />
          </div>
          <div>
            <Label>Ethnicity (optional)</Label>
            <Select onValueChange={(v) => setForm((f) => ({ ...f, ethnicity: v }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select ethnicity" />
              </SelectTrigger>
              <SelectContent>
                {options.ethnicity_options.map((o) => (
                  <SelectItem key={o} value={o}>{o}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="md:col-span-2 flex justify-end gap-3 mt-2">
            <Button type="submit" disabled={loading}>Create Profile</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

const SwipeDeck = ({ user, onExit }) => {
  const api = useApi();
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchCards = async () => {
    setLoading(true);
    try {
      const r = await api.get(`/placer/cards`, { params: { user_id: user.id, limit: 10 } });
      if ((r.data || []).length === 0) {
        // generate first batch via AI
        await api.post(`/placer/suggest`, { user_id: user.id, count: 8 });
        const r2 = await api.get(`/placer/cards`, { params: { user_id: user.id, limit: 10 } });
        setCards(r2.data || []);
      } else {
        setCards(r.data || []);
      }
    } catch (e) {
      console.error(e);
      toast({ title: "Error", description: e?.response?.data?.detail || "Failed to fetch cards" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
    
  }, []);

  const swipe = async (direction) => {
    if (cards.length === 0) return;
    const top = cards[0];
    setCards((c) => c.slice(1));
    try {
      await api.post(`/placer/swipe`, { user_id: user.id, card_id: top.id, direction });
      if (cards.length <= 3) {
        // top-up silently
        await api.post(`/placer/suggest`, { user_id: user.id, count: 6 });
        const r = await api.get(`/placer/cards`, { params: { user_id: user.id, limit: 10 } });
        setCards(r.data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="md:col-span-2 space-y-4">
        {loading && <div className="muted">Loading experiences…</div>}
        {!loading && cards.length === 0 && (
          <Card className="p-6">
            <CardTitle>No cards</CardTitle>
            <CardContent className="pt-4">No experiences available yet.</CardContent>
          </Card>
        )}
        {cards.slice(0, 1).map((c) => (
          <Card key={c.id} className="p-6 card-pop">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Badge variant="secondary">Predicted</Badge>
                {c.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="leading-relaxed">{c.description}</p>
              {c.rationale && (
                <p className="text-sm text-muted-foreground">Why: {c.rationale}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="flex md:flex-col gap-3 justify-center">
        <Button className="btn-left" variant="outline" onClick={() => swipe("left")}><ThumbsDown size={18} /> Not looking</Button>
        <Button className="btn-right" onClick={() => swipe("right")}><ThumbsUp size={18} /> Experienced</Button>
        <Button className="btn-up" variant="secondary" onClick={() => swipe("up")}><ArrowUp size={18} /> Want to</Button>
        <Button className="btn-down" variant="ghost" onClick={() => swipe("down")}><ArrowDown size={18} /> Had, don’t care</Button>
        <Button variant="outline" onClick={fetchCards}><Wand2 size={18} /> Refresh</Button>
        <Button variant="ghost" onClick={onExit}>Exit</Button>
      </div>
    </div>
  );
};

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const hello = async () => {
      try {
        await axios.get(`${API}/`);
      } catch (e) {
        console.error(e);
      }
    };
    hello();
  }, []);

  return (
    <BrowserRouter>
      <div className="container">
        <header className="py-6">
          <h1 className="brand">Life Explorer</h1>
          <p className="subtitle">See what people like you are doing — and discover what you might be missing.</p>
        </header>
        <main className="grid gap-6">
          {!user ? (
            <SignUp onCreated={setUser} />
          ) : (
            <SwipeDeck user={user} onExit={() => setUser(null)} />
          )}
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;