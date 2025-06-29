import React, { useState } from 'react';
import axios from 'axios';

interface PersonaData {
  name: string;
  summary: string;
  word_cloud: { [key: string]: number };
  sentiment_score: number;
  id: number;
}

interface PersonaResponse {
  id: number;
  persona: PersonaData;
}

export default function PersonaApp() {
  const [name, setName] = useState('');
  const [sample, setSample] = useState('');
  const [persona, setPersona] = useState<PersonaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [personaId, setPersonaId] = useState<number | null>(null);
  const [newSample, setNewSample] = useState('');

  const api = axios.create({ baseURL: 'http://localhost:8000' });

  const generatePersona = async () => {
    setLoading(true);
    try {
      const response = await api.post(`/persona/?name=${encodeURIComponent(name)}`, { text: sample });
      setPersona(response.data);
      setPersonaId(response.data.id);
    } catch (err) {
      alert('Error creating persona');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const addToPersona = async () => {
    if (!personaId) return;
    setLoading(true);
    try {
      const response = await api.post(`/persona/${personaId}/add_sample`, { text: newSample });
      setPersona(response.data);
      setNewSample('');
    } catch (err) {
      alert('Error updating persona');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Persona JSON Generator</h1>

      <div className="mb-6">
        <label className="block font-semibold">Persona Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} className="w-full p-2 border rounded mb-4" />

        <label className="block font-semibold">Writing Sample</label>
        <textarea value={sample} onChange={(e) => setSample(e.target.value)} className="w-full p-2 border rounded h-40 mb-4" />

        <button
          onClick={generatePersona}
          disabled={loading || !name || !sample}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Generate Persona
        </button>
      </div>

      {persona && (
        <div className="mb-6">
          <h2 className="text-2xl font-semibold mb-2">Persona JSON</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-x-auto text-sm">
            {JSON.stringify(persona.persona, null, 2)}
          </pre>

          <div className="mt-4">
            <label className="block font-semibold">Add More Sample Text</label>
            <textarea value={newSample} onChange={(e) => setNewSample(e.target.value)} className="w-full p-2 border rounded h-32 mb-4" />

            <button
              onClick={addToPersona}
              disabled={loading || !newSample}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              Add Sample to Persona
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
