import React from 'react';
import { Button } from "@/components/ui/button";
import { Download } from 'lucide-react';
import html2canvas from 'html2canvas';
import * as XLSX from 'xlsx';

interface ExportData {
  [key: string]: string | number | Date;
}

interface ExportButtonProps {
  targetRef: React.RefObject<HTMLElement>;
  type: 'chart' | 'table';
  data?: ExportData[];
  filename?: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({
  targetRef,
  type,
  data,
  filename = 'export'
}) => {
  const exportAsImage = async () => {
    if (!targetRef.current) return;

    try {
      const canvas = await html2canvas(targetRef.current);
      const image = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = image;
      link.download = `${filename}.png`;
      link.click();
    } catch (error) {
      console.error('Error exporting image:', error);
    }
  };

  const exportAsExcel = () => {
    if (!data) return;

    try {
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Data');
      XLSX.writeFile(wb, `${filename}.xlsx`);
    } catch (error) {
      console.error('Error exporting Excel:', error);
    }
  };

  const handleExport = () => {
    if (type === 'chart') {
      exportAsImage();
    } else {
      exportAsExcel();
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleExport}
      className="flex items-center gap-2"
    >
      <Download className="h-4 w-4" />
      Export {type === 'chart' ? 'Image' : 'Excel'}
    </Button>
  );
}; 