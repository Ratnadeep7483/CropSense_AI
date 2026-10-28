import { X } from "lucide-react";

interface ImagePreviewProps {
  imageUrl: string;
  onClear: () => void;
}

export default function ImagePreview({ imageUrl, onClear }: ImagePreviewProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-surface-200 bg-surface-50">
      <img
        src={imageUrl}
        alt="Uploaded crop image"
        className="mx-auto max-h-80 w-full object-contain"
      />
      <button
        onClick={onClear}
        className="absolute right-3 top-3 rounded-full bg-white/90 p-1.5 text-surface-600 shadow-sm backdrop-blur transition-colors hover:bg-white hover:text-surface-900"
        aria-label="Remove image"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
