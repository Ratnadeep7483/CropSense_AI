import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function PublicLayout() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar showMenu={false} />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
