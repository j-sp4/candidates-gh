export default function TopicCloud({ topics }) {
  if (!topics || topics.length === 0) {
    return <div className="text-gray-500 text-center py-10">No topic data available</div>;
  }

  // Calculate font sizes based on count
  const maxCount = Math.max(...topics.map(topic => topic.count));
  const minCount = Math.min(...topics.map(topic => topic.count));
  const fontSizeRange = [1, 2.5]; // rem units
  
  const calculateFontSize = (count) => {
    if (maxCount === minCount) return fontSizeRange[0];
    const normalized = (count - minCount) / (maxCount - minCount);
    return fontSizeRange[0] + normalized * (fontSizeRange[1] - fontSizeRange[0]);
  };

  // Generate random pastel colors
  const getRandomColor = () => {
    const hue = Math.floor(Math.random() * 360);
    return `hsl(${hue}, 70%, 80%)`;
  };

  return (
    <div className="flex flex-wrap justify-center gap-3 py-4">
      {topics.map((topic, index) => (
        <div 
          key={index}
          className="px-3 py-1 rounded-full transition-transform hover:scale-110"
          style={{ 
            fontSize: `${calculateFontSize(topic.count)}rem`,
            backgroundColor: getRandomColor(),
            cursor: 'pointer'
          }}
        >
          {topic.name}
        </div>
      ))}
    </div>
  );
} 