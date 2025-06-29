import React, { useState } from 'react';
import axios from 'axios';

interface PersonaData {
  id: number;
  persona: any; // Adjust this type based on the actual persona structure
}

export default function PersonaApp() {
  const [name, setName] = useState('');
  const [sample, setSample] = useState('');
  const [persona, setPersona] = useState<PersonaData | null>(null);
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
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-300 p-6 sm:p-8">
      <div className="max-w-4xl mx-auto bg-white shadow-2xl rounded-2xl p-6 sm:p-10">
        <h1 className="text-4xl font-bold mb-6 text-center text-gray-800">🧬 Persona JSON Generator</h1>

        <div className="mb-10">
          <label className="block font-medium text-lg text-gray-700 mb-2">Persona Name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 mb-4"
            placeholder="e.g., Hemingwayish"
          />

          <label className="block font-medium text-lg text-gray-700 mb-2">Writing Sample</label>
          <textarea
            value={sample}
            onChange={(e) => setSample(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 h-40 mb-4"
            placeholder="Paste a writing sample here..."
          />

          <button
            onClick={generatePersona}
            disabled={loading || !name || !sample}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition disabled:opacity-50"
          >
            Generate Persona
          </button>
        </div>

        {persona && (
          <div className="mb-10">
            <h2 className="text-2xl font-semibold mb-3 text-gray-800">🧠 Persona Output</h2>
            <pre className="bg-gray-900 text-green-300 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(persona.persona, null, 2)}
            </pre>

            <div className="mt-6">
              <label className="block font-medium text-lg text-gray-700 mb-2">Refine with Additional Sample</label>
              <textarea
                value={newSample}
                onChange={(e) => setNewSample(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 h-32 mb-4"
                placeholder="Add another sample to improve persona..."
              />

              <button
                onClick={addToPersona}
                disabled={loading || !newSample}
                className="px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition disabled:opacity-50"
              >
                Add Sample to Persona
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
