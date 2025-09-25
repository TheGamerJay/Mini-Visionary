import React from "react";

const STYLES = [
  { key: "fantasy", label: "Fantasy", img: "/assets/previews/fantasy.jpg" },
  { key: "scifi",   label: "Sci-Fi", img: "/assets/previews/scifi.jpg" },
  { key: "horror",  label: "Horror", img: "/assets/previews/horror.jpg" },
  { key: "romance", label: "Romance", img: "/assets/previews/romance.jpg" },
  { key: "action",  label: "Action", img: "/assets/previews/action.jpg" },
  { key: "anime",   label: "Anime", img: "/assets/previews/anime.jpg" },
];

export default function PosterStyleGallery({ onSelect, selectedStyle = "fantasy" }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-6">
      {STYLES.map(style => (
        <div
          key={style.key}
          onClick={() => onSelect(style.key)}
          className={`cursor-pointer rounded-lg overflow-hidden shadow-md hover:scale-105 transition-transform ${
            selectedStyle === style.key ? 'ring-2 ring-purple-500' : ''
          }`}
        >
          <img src={style.img} alt={style.label} className="w-full h-48 object-cover" />
          <div className="p-2 bg-gray-900 text-white text-center text-sm font-semibold">
            {style.label}
          </div>
        </div>
      ))}
    </div>
  );
}