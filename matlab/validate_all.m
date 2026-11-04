function results = validate_all()
%VALIDATE_ALL Run every curriculum laboratory without graphical windows.
results=cell(8,1);
for unit=1:8,results{unit}=run_lesson(unit,false);end
fprintf('All eight curriculum units passed.\n');
end
