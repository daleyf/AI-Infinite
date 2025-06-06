import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { ChevronLeft, ChevronRight, ChevronsLeft } from "lucide-react"; // 🆕
import { motion } from "framer-motion";

// -----------------------------------------------------------------------------
// Inline UI component replacements
// -----------------------------------------------------------------------------
const Button = ({ children, ...props }) => (
  <button
    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition disabled:opacity-50"
    {...props}
  >
    {children}
  </button>
);

const Card = ({ children, className = "" }) => (
  <div className={`bg-white border shadow rounded-xl ${className}`}>
    {children}
  </div>
);

const CardContent = ({ children, className = "" }) => (
  <div className={`p-4 ${className}`}>{children}</div>
);

// -----------------------------------------------------------------------------
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const fetchIteration = async (idx) => {
  const { data } = await axios.get(`${API_BASE}/iteration/${idx}`);
  return data;
};

const fetchMeta = async () => {
  const { data } = await axios.get(`${API_BASE}/iterations/meta`);
  return data;
};

export default function Dashboard() {
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [iteration, setIteration] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadMeta = useCallback(async () => {
    try {
      const meta = await fetchMeta();
      setTotal(meta.total_pages);
    } catch (err) {
      console.error("Failed to fetch meta", err);
    }
  }, []);

  const loadIteration = useCallback(async (idx) => {
    setLoading(true);
    try {
      const data = await fetchIteration(idx);
      setIteration(data);
    } catch (err) {
      console.error("Failed to fetch iteration", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMeta();
  }, [loadMeta]);

  useEffect(() => {
    loadIteration(page);
  }, [page, loadIteration]);

  const handlePrev = () => setPage((p) => Math.max(1, p - 1));
  const handleNext = () => setPage((p) => Math.min(total, p + 1));
  const handleJump = (e) => setPage(Number(e.target.value));
  const handleFirst = () => setPage(1); // 🆕 jump to first page

  if (loading || !iteration) {
    return (
      <div className="flex items-center justify-center h-screen">
        <span className="animate-pulse text-gray-500">⏳ Loading…</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-indigo-100 p-6"> {/* 🆕 Color upgrade */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* MAIN COLUMN */}
        <Card className="flex-1 shadow-xl rounded-2xl">
          <CardContent className="p-6 space-y-4">
            {/* Metadata bar */}
            <div className="text-sm text-indigo-800 font-medium">
              <strong>🌀 Iteration:</strong> {iteration.id} &nbsp;|&nbsp;
              <strong>🧠 Prompt:</strong> {iteration.prompt} &nbsp;|&nbsp;
              <strong>🔢 Tokens:</strong> {iteration.tokens.out}/{iteration.tokens.in}
            </div>

            {/* LLM output */}
            <motion.pre
              layout
              className="whitespace-pre-wrap font-mono overflow-auto leading-relaxed bg-white p-4 rounded-lg shadow-inner text-gray-800"
            >
              {iteration.text}
            </motion.pre>

            {/* Navigation controls */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4">
              <div className="flex gap-2">
                <Button onClick={handleFirst} disabled={page === 1}>
                  <ChevronsLeft className="h-4 w-4 mr-1" /> First
                </Button>
                <Button onClick={handlePrev} disabled={page === 1}>
                  <ChevronLeft className="h-4 w-4 mr-1" /> Prev
                </Button>
                <Button onClick={handleNext} disabled={page === total}>
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>

              <select
                className="px-3 py-2 rounded-lg border bg-white shadow"
                value={page}
                onChange={handleJump}
              >
                {Array.from({ length: total }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    Jump to {n}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* SIDEBAR */}
        <Card className="w-full lg:w-80 shadow-xl rounded-2xl bg-indigo-50">
          <CardContent className="p-6 space-y-3 text-sm text-indigo-900">
            <div>
              <strong>📚 Total iterations:</strong> {total}
            </div>
            <div>
              <strong>📖 Current page:</strong> {page}/{total}
            </div>
            <div>
              <strong>💰 Cost:</strong> ${iteration.cost?.toFixed(4) ?? "N/A"}
            </div>
            <div>
              <strong>⏱️ Runtime:</strong> {iteration.total_runtime_seconds?.toFixed(2)}s
            </div>
            <div className="text-indigo-400 pt-3">
              📊 Memory stats coming soon...
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
