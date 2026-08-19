"use client";

import { useEffect, useRef, useState } from "react";

import { ChevronLeftIcon, ChevronRightIcon } from "@/components/icons";

// Mismo comportamiento ya validado en el mockup (docs/design/amza_workspace_mockup/template.html,
// openDateTimePicker) -- calendario flotante, luego hora AM/PM -- portado a React.
const MONTH_NAMES_ES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];
const DOW_ES = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

export function DateTimePicker({
  onSelect,
  onClose,
}: {
  onSelect: (date: Date) => void;
  onClose: () => void;
}) {
  const now = new Date();
  const [view, setView] = useState<"calendar" | "time">("calendar");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState("00");
  const [ampm, setAmpm] = useState<"AM" | "PM">(now.getHours() >= 12 ? "PM" : "AM");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [onClose]);

  const todayMid = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const first = new Date(year, month, 1);
  const offset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  function prevMonth() {
    if (month === 0) {
      setMonth(11);
      setYear((y) => y - 1);
    } else {
      setMonth((m) => m - 1);
    }
  }

  function nextMonth() {
    if (month === 11) {
      setMonth(0);
      setYear((y) => y + 1);
    } else {
      setMonth((m) => m + 1);
    }
  }

  function confirm() {
    if (selectedDay === null) return;
    let h24 = hour % 12;
    if (ampm === "PM") h24 += 12;
    onSelect(new Date(year, month, selectedDay, h24, Number(minute)));
  }

  return (
    <div
      ref={containerRef}
      className="absolute z-30 mt-2 w-60 rounded-xl border bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-900"
    >
      {view === "calendar" ? (
        <div>
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              onClick={prevMonth}
              aria-label="Mes anterior"
              className="rounded p-1 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ChevronLeftIcon className="h-4 w-4" />
            </button>
            <span className="text-xs font-bold">
              {MONTH_NAMES_ES[month]} {year}
            </span>
            <button
              type="button"
              onClick={nextMonth}
              aria-label="Mes siguiente"
              className="rounded p-1 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ChevronRightIcon className="h-4 w-4" />
            </button>
          </div>
          <div className="mb-1 grid grid-cols-7 text-center text-[9px] text-gray-400">
            {DOW_ES.map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-0.5">
            {Array.from({ length: offset }).map((_, i) => (
              <span key={`empty-${i}`} />
            ))}
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
              const thisDate = new Date(year, month, day);
              const past = thisDate < todayMid;
              const isToday = thisDate.getTime() === todayMid.getTime();
              return (
                <button
                  key={day}
                  type="button"
                  disabled={past}
                  onClick={() => {
                    setSelectedDay(day);
                    setView("time");
                  }}
                  className={`rounded p-1.5 text-[11px] ${
                    past
                      ? "text-gray-300 dark:text-gray-700"
                      : "hover:bg-gray-100 dark:hover:bg-gray-800"
                  } ${isToday ? "font-bold text-emerald-700 dark:text-emerald-400" : ""}`}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div>
          <p className="mb-3 text-center text-xs font-bold">
            {selectedDay} {MONTH_NAMES_ES[month].slice(0, 3).toLowerCase()} {year}
          </p>
          <div className="mb-3 flex items-center justify-center gap-1">
            <select
              value={hour}
              onChange={(e) => setHour(Number(e.target.value))}
              className="rounded border px-1.5 py-1 text-xs dark:bg-gray-800"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => (
                <option key={h} value={h}>
                  {h}
                </option>
              ))}
            </select>
            <span>:</span>
            <select
              value={minute}
              onChange={(e) => setMinute(e.target.value)}
              className="rounded border px-1.5 py-1 text-xs dark:bg-gray-800"
            >
              {["00", "15", "30", "45"].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <div className="ml-1 flex overflow-hidden rounded border">
              {(["AM", "PM"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setAmpm(v)}
                  className={`px-2 py-1 text-[10px] font-bold ${
                    ampm === v ? "bg-emerald-600 text-white" : ""
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => setView("calendar")}
              className="flex-1 rounded border py-1.5 text-xs"
            >
              Atrás
            </button>
            <button
              type="button"
              onClick={confirm}
              className="flex-1 rounded bg-emerald-600 py-1.5 text-xs font-bold text-white"
            >
              Listo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
