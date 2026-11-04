function results = validate_all()
%VALIDATE_ALL Run every curriculum laboratory without graphical windows.
results=cell(9,1);
for unit=1:9,results{unit}=run_lesson(unit,false);end
validate_markov();
fprintf('All nine laboratory units passed.\n');
end
