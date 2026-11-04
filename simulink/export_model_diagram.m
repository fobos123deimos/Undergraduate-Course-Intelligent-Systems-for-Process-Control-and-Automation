function export_model_diagram(name,path)
%EXPORT_MODEL_DIAGRAM Open a diagram before printing; requires a display.
% Linux CI starts an Xvfb virtual display before MATLAB. Numerical simulation
% works without a display, but Simulink's print command does not.
% The calling validator owns and closes the model through its onCleanup.
open_system(name);
set_param(name,'ZoomFactor','FitSystem');
print(['-s' name],'-dpng','-r120',path);
end
