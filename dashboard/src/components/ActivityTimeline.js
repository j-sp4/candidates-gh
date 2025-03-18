'use client';

import { useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function ActivityTimeline({ timelineData }) {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [
      {
        label: 'Repositories Created',
        data: [],
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgb(54, 162, 235)',
        borderWidth: 1,
      },
    ],
  });

  useEffect(() => {
    if (timelineData && timelineData.length > 0) {
      // Format dates for display
      const formattedDates = timelineData.map(item => {
        const [year, month] = item.date.split('-');
        return `${getMonthName(month)} ${year}`;
      });
      
      setChartData({
        labels: formattedDates,
        datasets: [
          {
            label: 'Repositories Created',
            data: timelineData.map(item => item.count),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1,
          },
        ],
      });
    }
  }, [timelineData]);

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Repository Creation Timeline',
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            return context[0].label;
          },
          label: function(context) {
            return `${context.parsed.y} repositories created`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Repositories'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Month/Year'
        }
      }
    }
  };

  // Helper function to get month name
  function getMonthName(monthNumber) {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return months[parseInt(monthNumber) - 1];
  }

  if (!timelineData || timelineData.length === 0) {
    return <div className="text-gray-500 text-center py-10">No timeline data available</div>;
  }

  return (
    <div className="h-80">
      <Bar data={chartData} options={options} />
    </div>
  );
} 