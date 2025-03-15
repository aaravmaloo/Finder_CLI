use pyo3::prelude::*;
use pyo3::types::PyModule;

fn main() -> PyResult<()> {

    pyo3::prepare_freethreaded_python();

    // Run Python code within the GIL
    Python::with_gil(|py| {

        let sys = PyModule::import(py, "sys")?;
        sys.getattr("path")?
            .call_method1("append", (r"C:\Users\Aarav Maloo\Desktop\Finder_CLI\src",))?;


        let curses = PyModule::import(py, "curses")?;


        let interface = PyModule::import(py, "interface")?;


        let main_func = interface.getattr("main")?;


        let wrapper = curses.getattr("wrapper")?;
        wrapper.call1((main_func,))?;

        Ok(())
    })
}