import { Outlet } from "react-router-dom";
import TopNav from "./TopNav";

const Layout = () => (
  <div className="min-h-screen bg-background">
    <TopNav />
    <Outlet />
  </div>
);

export default Layout;
