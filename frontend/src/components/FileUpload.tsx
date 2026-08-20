import React, { useCallback } from 'react';
import { useDropzone, Accept } from 'react-dropzone';
import { UploadCloud, File as FileIcon } from 'lucide-react';
import { clsx } from 'clsx';

interface Props {
  onDrop: (files: File[]) => void;
  accept?: Accept;
  maxSize?: number;
  label?: string;
  sublabel?: string;
  file?: File | null;
}

export const FileUpload: React.FC<Props> = ({ 
  onDrop, 
  accept, 
  maxSize = 10485760, 
  label = 'Drag & drop a file here', 
  sublabel = 'or click to select',
  file
}) => {
  const onDropCallback = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onDrop(acceptedFiles);
    }
  }, [onDrop]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropCallback,
    accept,
    maxSize,
    multiple: false
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
        isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
      )}
    >
      <input {...getInputProps()} />
      {file ? (
        <div className="flex flex-col items-center">
          <FileIcon className="h-12 w-12 text-primary-500 mb-3" />
          <p className="text-sm font-medium text-gray-900">{file.name}</p>
          <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <UploadCloud className="h-12 w-12 text-gray-400 mb-3" />
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-xs text-gray-500 mt-1">{sublabel}</p>
        </div>
      )}
    </div>
  );
};
