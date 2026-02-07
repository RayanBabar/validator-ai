import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import Landing from "./pages/Landing";
import Submit from "./pages/Submit";
import Interview from "./pages/Interview";
import Report from "./pages/Report";
import Upgrade from "./pages/Upgrade";
import Processing from "./pages/Processing";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/submit" element={<Submit />} />
            <Route path="/interview/:threadId" element={<Interview />} />
            <Route path="/report/:threadId" element={<Report />} />
            <Route path="/upgrade/:threadId" element={<Upgrade />} />
            <Route path="/processing/:threadId" element={<Processing />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
