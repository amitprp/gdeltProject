import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { countries } from "@/lib/countries";

interface CountrySelectProps {
  value: string;
  onChange: (value: string) => void;
}

export function CountrySelect({ value, onChange }: CountrySelectProps) {
  return (
    <Select
      value={value}
      onValueChange={onChange}
    >
      <SelectTrigger>
        <SelectValue placeholder="Select a country" />
      </SelectTrigger>
      <SelectContent>
        {countries.map((country) => (
          <SelectItem key={country.code} value={country.name}>
            {country.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
} 