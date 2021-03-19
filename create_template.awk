BEGIN {
	
}

$0 !~ /^#|__/{
	if (length($0)>0)
	{		
		split($0, array, "=")
		print(array[1]"={"array[1]"_VAL}")
		next
	}
}

{
	print($0)
}
