import { useCallback, useState } from "react";
import { Upload, Camera } from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";

interface ImageUploaderProps {
  onImageSelect: (file: File) => void;
}

export default function ImageUploader({ onImageSelect }: ImageUploaderProps) {
  const { t } = useLanguage();
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (file.type.startsWith("image/")) {
        onImageSelect(file);
      }
    },
    [onImageSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all ${
        isDragging
          ? "border-primary-500 bg-primary-50"
          : "border-surface-300 bg-surface-50 hover:border-primary-400 hover:bg-primary-50/50"
      }`}
    >
      <div className="mb-4 rounded-2xl bg-surface-100 p-4">
        <Upload className="h-8 w-8 text-surface-400" />
      </div>
      <p className="mb-1 text-lg font-semibold text-surface-800">
        {t.uploadPlantImage}
      </p>
      <p className="mb-6 text-sm text-surface-500">{t.dragDropText}</p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-primary-700 hover:-translate-y-0.5">
          <Upload className="h-4 w-4" />
          {t.chooseImage}
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </label>
        <button
          className="inline-flex items-center gap-2 rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700 shadow-sm transition-all hover:bg-surface-50 hover:-translate-y-0.5"
          onClick={() => {
            /* Camera UI placeholder */
          }}
        >
          <Camera className="h-4 w-4" />
          {t.useCamera}
        </button>
      </div>
    </div>
  );
}
