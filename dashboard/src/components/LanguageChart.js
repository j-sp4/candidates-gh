'use client';

import { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

// Color palette for languages
const COLORS = [
  '#2563eb', // blue-600
  '#7c3aed', // violet-600
  '#db2777', // pink-600
  '#ea580c', // orange-600
  '#16a34a', // green-600
  '#ca8a04', // yellow-600
  '#0891b2', // cyan-600
  '#4f46e5', // indigo-600
  '#be123c', // rose-700
  '#15803d', // green-700
];

export default function LanguageChart({ languages }) {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [
      {
        data: [],
        backgroundColor: [],
        borderColor: [],
        borderWidth: 1,
      },
    ],
  });

  useEffect(() => {
    if (languages && languages.length > 0) {
      const topLanguages = languages.slice(0, 10);
      
      setChartData({
        labels: topLanguages.map(lang => lang.name),
        datasets: [
          {
            data: topLanguages.map(lang => lang.count),
            backgroundColor: COLORS.slice(0, topLanguages.length),
            borderColor: COLORS.slice(0, topLanguages.length).map(color => color + '80'),
            borderWidth: 1,
          },
        ],
      });
    }
  }, [languages]);

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          boxWidth: 15,
          padding: 15,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.raw || 0;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = Math.round((value / total) * 100);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    },
  };

  if (!languages || languages.length === 0) {
    return <div className="text-gray-500 text-center py-10">No language data available</div>;
  }

  return (
    <div className="h-64">
      <Pie data={chartData} options={options} />
    </div>
  );
} 