import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App shell", () => {
  it("renders application heading", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "AI Crypto Advisor" })).toBeInTheDocument();
  });
});
