// components/BrandTitle.tsx
import { Text, View } from 'react-native';
import { useColorScheme } from 'react-native';
import { Colors } from '../constants/Colors';

type BrandTitleProps = {
  text: string;
  highlight: string;
};

export default function BrandTitle({ text, highlight }: BrandTitleProps) {
  const colorScheme = useColorScheme();
  const logoBlue = Colors[colorScheme ?? 'light'].logoBlue;

  return (
    <View className="flex flex-row flex-wrap items-center">
      <Text className="text-6xl font-extrabold text-black tracking-tight leading-tight">
        {text}&nbsp;
      </Text>
      <Text
        className="text-6xl font-extrabold tracking-tight leading-tight"
        style={{ color: logoBlue }}
      >
        {highlight}
      </Text>
    </View>
  );
}
