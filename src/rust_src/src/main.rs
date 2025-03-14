use pyo3::prelude::*;
use pyo3::types::PyModule;

fn main() -> PyResult<()> {
    // Initialize the Python interpreter
    pyo3::prepare_freethreaded_python();

    // Run Python code within the GIL
    Python::with_gil(|py| {
        // Add the src directory to sys.path to find interface.py
        let sys = PyModule::import(py, "sys")?;
        sys.getattr("path")?
            .call_method1("append", (r"C:\Users\Aarav Maloo\Desktop\Finder_CLI\src",))?;

        // Import the curses module
        let curses = PyModule::import(py, "curses")?;

        // Import the interface module
        let interface = PyModule::import(py, "interface")?;

        // Get the main function from interface.py
        let main_func = interface.getattr("main")?;

        // Call curses.wrapper(main) to properly initialize the curses environment
        let wrapper = curses.getattr("wrapper")?;
        wrapper.call1((main_func,))?;

        Ok(())
    })
}