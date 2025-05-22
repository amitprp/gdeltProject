import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BackToHome = () => {
  const navigate = useNavigate();

  return (
    <Button 
      onClick={() => navigate('/')} 
      className="mb-6 bg-purple-600 hover:bg-purple-700 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2"
    >
      <ArrowLeft className="h-4 w-4" /> Back to Dashboard
    </Button>
  );
};

export default BackToHome; 