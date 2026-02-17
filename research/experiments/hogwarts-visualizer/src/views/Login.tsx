import React, { useState } from 'react';
import { useAuth } from '../contexts';
import { useHouse } from '../contexts/HouseContext';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, error: authError } = useAuth();
  const { activeHouse } = useHouse();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await login({ username, password });
    } catch (err) {
      console.error('Login failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // House-based styling
  const houseColors: Record<string, string> = {
    Gryffindor: 'from-red-700 to-yellow-600',
    Slytherin: 'from-green-800 to-gray-500',
    Hufflepuff: 'from-yellow-400 to-black',
    Ravenclaw: 'from-blue-800 to-gray-400',
  };

  const bgGradient = houseColors[activeHouse] || 'from-indigo-900 to-purple-900';

  return (
    <div className={`min-h-screen flex items-center justify-center bg-gradient-to-br ${bgGradient} p-4 transition-all duration-1000`}>
      <div className="max-w-md w-full bg-white/10 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/20 transform hover:scale-[1.01] transition-transform">
        <div className="text-center mb-10">
          <div className="inline-block p-4 rounded-full bg-white/20 mb-4 animate-float">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2 font-serif tracking-wider">Hogwarts Registry</h1>
          <p className="text-white/60">Enter your credentials to access the Great Hall</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2 ml-1" htmlFor="username">
              Wizard Name
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-3 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/40 transition-all"
              placeholder="e.g. Harry Potter"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/80 mb-2 ml-1" htmlFor="password">
              Secret Incantation
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-3 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/40 transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          {authError && (
            <div className="p-4 rounded-2xl bg-red-500/20 border border-red-500/50 text-red-200 text-sm animate-shake">
              {authError}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full py-4 rounded-2xl text-white font-bold text-lg shadow-lg transform active:scale-95 transition-all
              ${isSubmitting ? 'bg-white/10 cursor-not-allowed' : 'bg-gradient-to-r hover:opacity-90 active:opacity-100'}
              ${bgGradient} border border-white/20`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Casting Spell...
              </span>
            ) : 'Cast Alohomora'}
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-white/10 text-center">
          <p className="text-white/40 text-sm">
            Forging keys for the {activeHouse} House
          </p>
        </div>
      </div>
    </div>
  );
};
